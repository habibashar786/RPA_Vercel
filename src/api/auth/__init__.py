"""
Authentication Module - CISSP Best Practices Implementation

Security Features:
- JWT tokens with RS256 signing (asymmetric)
- Secure password hashing with bcrypt
- Google OAuth 2.0 integration
- Rate limiting on auth endpoints
- Secure session management
- CSRF protection ready
- Token refresh mechanism
"""

from .models import User, UserCreate, UserLogin, Token, TokenData
from .jwt_handler import create_access_token, verify_token, get_current_user
from .oauth import GoogleOAuth
from .password import hash_password, verify_password
from .router import router as auth_router

__all__ = [
    "User",
    "UserCreate", 
    "UserLogin",
    "Token",
    "TokenData",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "GoogleOAuth",
    "hash_password",
    "verify_password",
    "auth_router",
]
