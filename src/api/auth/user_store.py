"""
User Store - In-Memory Database for Development

In production, replace with:
- PostgreSQL with SQLAlchemy
- MongoDB with Motor
- Redis for session storage

CISSP Notes:
- Passwords stored as bcrypt hashes only
- User IDs are UUIDs (non-sequential)
- Sensitive operations are logged
"""

from datetime import datetime
from typing import Dict, Optional
import uuid
from loguru import logger

from .models import UserInDB, UserCreate
from .password import hash_password


class UserStore:
    """
    In-memory user store for development.
    
    Thread-safe for basic operations.
    Replace with proper database in production.
    """
    
    def __init__(self):
        self._users: Dict[str, UserInDB] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
        self._google_id_index: Dict[str, str] = {}  # google_id -> user_id
        logger.info("UserStore initialized (in-memory)")
    
    async def create_user(
        self,
        user_data: UserCreate,
        google_id: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_verified: bool = False,
    ) -> UserInDB:
        """
        Create a new user.
        
        Args:
            user_data: User registration data
            google_id: Google OAuth ID (if OAuth signup)
            avatar_url: Avatar URL from OAuth
            is_verified: Email verification status
            
        Returns:
            Created user
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if user_data.email.lower() in self._email_index:
            raise ValueError("Email already registered")
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Hash password (empty string for OAuth users)
        hashed_password = ""
        if user_data.password:
            hashed_password = hash_password(user_data.password)
        
        # Create user record
        user = UserInDB(
            id=user_id,
            email=user_data.email.lower(),
            name=user_data.name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=is_verified,
            subscription_tier="free",
            proposals_generated=0,
            created_at=datetime.utcnow(),
            google_id=google_id,
            avatar_url=avatar_url,
        )
        
        # Store user
        self._users[user_id] = user
        self._email_index[user.email] = user_id
        
        if google_id:
            self._google_id_index[google_id] = user_id
        
        logger.info(f"Created user: {user_id} ({user.email})")
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        user_id = self._email_index.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[UserInDB]:
        """Get user by Google OAuth ID."""
        user_id = self._google_id_index.get(google_id)
        if user_id:
            return self._users.get(user_id)
        return None
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[UserInDB]:
        """
        Update user fields.
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
            
        Returns:
            Updated user or None if not found
        """
        user = self._users.get(user_id)
        if not user:
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self._users[user_id] = user
        
        logger.debug(f"Updated user: {user_id}")
        return user
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        user = self._users.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self._users[user_id] = user
    
    async def increment_proposals_count(self, user_id: str) -> None:
        """Increment user's proposals generated count."""
        user = self._users.get(user_id)
        if user:
            user.proposals_generated += 1
            self._users[user_id] = user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (soft delete in production).
        
        Returns:
            True if deleted, False if not found
        """
        user = self._users.get(user_id)
        if not user:
            return False
        
        # Remove from indexes
        if user.email in self._email_index:
            del self._email_index[user.email]
        
        if user.google_id and user.google_id in self._google_id_index:
            del self._google_id_index[user.google_id]
        
        # Remove user
        del self._users[user_id]
        
        logger.info(f"Deleted user: {user_id}")
        return True
    
    def get_user_count(self) -> int:
        """Get total user count."""
        return len(self._users)


# Global user store instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Get or create the global user store instance."""
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store
