"""
Google OAuth 2.0 Integration - CISSP Best Practices

Security Features:
- ID Token verification with Google's public keys
- Audience validation
- Issuer validation
- Token expiration check
- Nonce verification (when implemented)
"""

import os
from typing import Optional, Dict, Any
import httpx
from loguru import logger
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from .models import User, UserInDB


class GoogleOAuth:
    """
    Google OAuth 2.0 handler.
    
    CISSP Security Considerations:
    - Validates token signature against Google's public keys
    - Checks token expiration
    - Validates audience (client ID)
    - Validates issuer (accounts.google.com)
    """
    
    # Google OAuth Configuration - Load fresh each time
    @classmethod
    def get_client_id(cls) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "")
    
    @classmethod  
    def get_client_secret(cls) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    @classmethod
    async def verify_google_token(cls, credential: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token and extract user info.
        
        Args:
            credential: JWT token from Google Sign-In
            
        Returns:
            Dict with user info or None if verification fails
        """
        client_id = cls.get_client_id()
        logger.info(f"Verifying Google token with client_id: {client_id[:20]}...")
        
        if not client_id:
            logger.error("GOOGLE_CLIENT_ID not configured")
            return None
            
        try:
            # Verify the token with Google's public keys
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
            
            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.warning(f"Invalid token issuer: {idinfo['iss']}")
                return None
            
            # Extract user information
            user_info = {
                "google_id": idinfo['sub'],
                "email": idinfo['email'],
                "email_verified": idinfo.get('email_verified', False),
                "name": idinfo.get('name', ''),
                "given_name": idinfo.get('given_name', ''),
                "family_name": idinfo.get('family_name', ''),
                "picture": idinfo.get('picture', ''),
                "locale": idinfo.get('locale', ''),
            }
            
            logger.info(f"Google token verified for: {user_info['email']}")
            return user_info
            
        except ValueError as e:
            logger.warning(f"Google token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying Google token: {e}")
            return None
    
    @classmethod
    async def verify_google_token_fallback(cls, credential: str) -> Optional[Dict[str, Any]]:
        """
        Fallback verification using Google's tokeninfo endpoint.
        
        Use this when google-auth library is not available.
        
        Args:
            credential: JWT token from Google Sign-In
            
        Returns:
            Dict with user info or None if verification fails
        """
        try:
            async with httpx.AsyncClient() as client:
                # Verify with Google's tokeninfo endpoint
                response = await client.get(
                    cls.GOOGLE_TOKEN_INFO_URL,
                    params={"id_token": credential},
                )
                
                if response.status_code != 200:
                    logger.warning(f"Google tokeninfo returned {response.status_code}")
                    return None
                
                idinfo = response.json()
                
                # Verify audience
                if idinfo.get('aud') != cls.get_client_id():
                    logger.warning("Token audience mismatch")
                    return None
                
                # Extract user information
                user_info = {
                    "google_id": idinfo['sub'],
                    "email": idinfo['email'],
                    "email_verified": idinfo.get('email_verified', 'true') == 'true',
                    "name": idinfo.get('name', ''),
                    "picture": idinfo.get('picture', ''),
                }
                
                logger.info(f"Google token verified (fallback) for: {user_info['email']}")
                return user_info
                
        except Exception as e:
            logger.error(f"Google token verification (fallback) failed: {e}")
            return None
    
    @classmethod
    async def get_user_info_with_access_token(cls, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info using an OAuth access token.
        
        Use this after OAuth code exchange flow.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dict with user info or None if request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    cls.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if response.status_code != 200:
                    logger.warning(f"Google userinfo returned {response.status_code}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get Google user info: {e}")
            return None
    
    @classmethod
    def create_user_from_google(cls, google_info: Dict[str, Any], user_id: str) -> UserInDB:
        """
        Create a UserInDB model from Google user info.
        
        Args:
            google_info: User info from Google
            user_id: Generated user ID
            
        Returns:
            UserInDB model
        """
        from datetime import datetime
        
        return UserInDB(
            id=user_id,
            email=google_info['email'],
            name=google_info.get('name', google_info['email'].split('@')[0]),
            hashed_password="",  # No password for OAuth users
            is_active=True,
            is_verified=google_info.get('email_verified', False),
            subscription_tier="free",
            proposals_generated=0,
            created_at=datetime.utcnow(),
            google_id=google_info['google_id'],
            avatar_url=google_info.get('picture'),
        )
