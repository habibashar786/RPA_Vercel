"""
Authentication Router - FastAPI Endpoints

CISSP Security Features:
- Rate limiting ready (add slowapi in production)
- Input validation via Pydantic
- Secure error messages (no information leakage)
- Audit logging for auth events
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger

from .models import (
    User,
    UserCreate,
    UserLogin,
    Token,
    TokenData,
    GoogleAuthRequest,
    RefreshTokenRequest,
    AuthResponse,
    PasswordResetRequest,
)
from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_token_expiry_seconds,
)
from .password import verify_password, hash_password
from .oauth import GoogleOAuth
from .user_store import get_user_store, UserStore


router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_store() -> UserStore:
    """Dependency to get user store."""
    return get_user_store()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    store: UserStore = Depends(get_store),
):
    """
    Register a new user.
    
    Security:
    - Password strength validation in model
    - Email uniqueness check
    - Password hashed before storage
    """
    try:
        # Create user
        user = await store.create_user(user_data)
        
        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        logger.info(f"New user registered: {user.email}")
        
        return AuthResponse(
            token=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=get_token_expiry_seconds(),
            ),
            user=User(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                subscription_tier=user.subscription_tier,
                proposals_generated=user.proposals_generated,
                avatar_url=user.avatar_url,
                created_at=user.created_at,
            ),
            message="Registration successful",
        )
        
    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    store: UserStore = Depends(get_store),
):
    """
    Login with email and password.
    
    Security:
    - Constant-time password comparison
    - Generic error message (no user enumeration)
    - Login attempt logging
    """
    # Generic error to prevent user enumeration
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get user
    user = await store.get_user_by_email(credentials.email)
    
    if not user:
        logger.warning(f"Login attempt for non-existent email: {credentials.email}")
        raise auth_error
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Invalid password for user: {user.email}")
        raise auth_error
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # Update last login
    await store.update_last_login(user.id)
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    
    logger.info(f"User logged in: {user.email}")
    
    return AuthResponse(
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
        ),
        user=User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            subscription_tier=user.subscription_tier,
            proposals_generated=user.proposals_generated,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        ),
        message="Login successful",
    )


@router.get("/debug/google-config")
async def debug_google_config():
    """
    Debug endpoint to verify Google OAuth configuration.
    Remove in production!
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()  # Ensure .env is loaded
    
    client_id = os.getenv("GOOGLE_CLIENT_ID", "NOT_SET")
    return {
        "client_id_prefix": client_id[:30] + "..." if len(client_id) > 30 else client_id,
        "client_id_set": bool(client_id and client_id != "NOT_SET" and "your_google" not in client_id.lower()),
        "client_id_full_length": len(client_id),
    }


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: GoogleAuthRequest,
    store: UserStore = Depends(get_store),
):
    """
    Authenticate with Google OAuth.
    
    Security:
    - Token verified with Google's public keys
    - Creates or links user account
    - Email verification status from Google
    """
    # Verify Google token
    google_info = await GoogleOAuth.verify_google_token(request.credential)
    
    if not google_info:
        # Try fallback verification
        google_info = await GoogleOAuth.verify_google_token_fallback(request.credential)
    
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        )
    
    # Check if user exists by Google ID
    user = await store.get_user_by_google_id(google_info['google_id'])
    
    if not user:
        # Check if user exists by email
        user = await store.get_user_by_email(google_info['email'])
        
        if user:
            # Link Google account to existing user
            await store.update_user(
                user.id,
                google_id=google_info['google_id'],
                avatar_url=google_info.get('picture'),
                is_verified=True,
            )
            logger.info(f"Linked Google account to existing user: {user.email}")
        else:
            # Create new user
            user_data = UserCreate(
                email=google_info['email'],
                name=google_info.get('name', google_info['email'].split('@')[0]),
                password="OAuth_User_No_Password_Required_123!",  # Placeholder, won't be used
            )
            user = await store.create_user(
                user_data,
                google_id=google_info['google_id'],
                avatar_url=google_info.get('picture'),
                is_verified=google_info.get('email_verified', False),
            )
            # Clear the placeholder password hash since OAuth users don't use passwords
            await store.update_user(user.id, hashed_password="")
            logger.info(f"Created new user from Google: {user.email}")
    
    # Update last login
    await store.update_last_login(user.id)
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    
    logger.info(f"Google auth successful: {user.email}")
    
    return AuthResponse(
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
        ),
        user=User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            subscription_tier=user.subscription_tier,
            proposals_generated=user.proposals_generated,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        ),
        message="Google authentication successful",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    store: UserStore = Depends(get_store),
):
    """
    Refresh access token using refresh token.
    
    Security:
    - Validates refresh token type
    - Issues new access token only
    - Checks if user still exists and is active
    """
    try:
        # Verify refresh token
        token_data = verify_token(request.refresh_token, expected_type="refresh")
        
        # Get user to verify still exists and active
        user = await store.get_user_by_id(token_data.user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Generate new access token
        access_token = create_access_token(user.id, user.email)
        
        logger.debug(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/profile", response_model=User)
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    store: UserStore = Depends(get_store),
):
    """
    Get current user's profile.
    
    Requires valid access token.
    """
    user = await store.get_user_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        subscription_tier=user.subscription_tier,
        proposals_generated=user.proposals_generated,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Logout user.
    
    In production, add token to blacklist.
    Client should discard tokens.
    """
    logger.info(f"User logged out: {current_user.email}")
    
    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    store: UserStore = Depends(get_store),
):
    """
    Request password reset email.
    
    Security:
    - Always returns success (prevents user enumeration)
    - In production, sends email with reset link
    """
    user = await store.get_user_by_email(request.email)
    
    if user:
        # In production: generate reset token and send email
        logger.info(f"Password reset requested for: {request.email}")
    else:
        # Log but don't reveal user doesn't exist
        logger.debug(f"Password reset requested for non-existent email")
    
    # Always return success to prevent enumeration
    return {
        "message": "If an account exists with this email, a reset link has been sent"
    }


@router.get("/verify-token")
async def verify_user_token(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Verify if current token is valid.
    
    Returns token data if valid.
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "expires_at": current_user.exp.isoformat(),
    }
