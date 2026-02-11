"""
JWT Token Handler - CISSP Best Practices

Security Features:
- HS256 signing with strong secret
- Short-lived access tokens (15 minutes)
- Longer-lived refresh tokens (7 days)
- Token type validation
- Secure token extraction from headers
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

from .models import TokenData, User, UserInDB


# JWT Configuration
# In production, use environment variable: os.getenv("JWT_SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(64))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    CISSP Notes:
    - Short expiration time limits exposure window
    - Contains minimal user data (no sensitive info)
    - Signed with HS256 (symmetric, fast)
    
    Args:
        user_id: User's unique identifier
        email: User's email
        expires_delta: Custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug(f"Created access token for user: {user_id}")
    
    return token


def create_refresh_token(user_id: str, email: str) -> str:
    """
    Create a JWT refresh token.
    
    CISSP Notes:
    - Longer expiration for user convenience
    - Should be stored securely (httpOnly cookie)
    - Can be revoked via token blacklist
    
    Args:
        user_id: User's unique identifier
        email: User's email
        
    Returns:
        str: Encoded JWT refresh token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug(f"Created refresh token for user: {user_id}")
    
    return token


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        expected_type: Expected token type (access or refresh)
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type", "access")
        exp = payload.get("exp")
        iat = payload.get("iat")
        
        if user_id is None or email is None:
            logger.warning("Token missing required claims")
            raise credentials_exception
        
        if token_type != expected_type:
            logger.warning(f"Token type mismatch: expected {expected_type}, got {token_type}")
            raise credentials_exception
        
        return TokenData(
            user_id=user_id,
            email=email,
            exp=datetime.fromtimestamp(exp, tz=timezone.utc),
            iat=datetime.fromtimestamp(iat, tz=timezone.utc),
            token_type=token_type,
        )
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_token(credentials.credentials, expected_type="access")


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> Optional[TokenData]:
    """
    Optional authentication - returns None if not authenticated.
    """
    if credentials is None:
        return None
    
    try:
        return verify_token(credentials.credentials, expected_type="access")
    except HTTPException:
        return None


def get_token_expiry_seconds() -> int:
    """Get access token expiry in seconds."""
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
