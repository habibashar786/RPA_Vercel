"""
User and Authentication Models - Pydantic schemas

CISSP Considerations:
- Minimum password complexity enforced
- Email validation
- No sensitive data exposure in responses
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """User registration model with password validation."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        CISSP-compliant password validation:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserInDB(UserBase):
    """User model as stored in database."""
    id: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    subscription_tier: str = "free"
    proposals_generated: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # OAuth fields
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None


class User(UserBase):
    """User model for API responses (no sensitive data)."""
    id: str
    is_active: bool = True
    is_verified: bool = False
    subscription_tier: str = "free"
    proposals_generated: int = 0
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(User):
    """Extended user profile."""
    proposals: List[str] = []  # List of proposal IDs
    last_login: Optional[datetime] = None


class Token(BaseModel):
    """JWT Token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str
    exp: datetime
    iat: datetime
    token_type: str = "access"  # access or refresh


class GoogleAuthRequest(BaseModel):
    """Google OAuth credential request."""
    credential: str  # JWT from Google Sign-In


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Same validation as UserCreate."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class AuthResponse(BaseModel):
    """Standard authentication response."""
    token: Token
    user: User
    message: str = "Authentication successful"
