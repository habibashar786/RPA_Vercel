"""
Password Hashing Utilities - CISSP Best Practices

Security Features:
- bcrypt with configurable work factor
- Automatic salt generation
- Timing-safe comparison
"""

import bcrypt
from typing import Tuple
import secrets
import hashlib


# Work factor for bcrypt (12 is recommended for production)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    CISSP Notes:
    - Uses bcrypt with automatic salt generation
    - Work factor of 12 provides ~300ms hashing time
    - Salt is embedded in the hash output
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password with embedded salt
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    CISSP Notes:
    - Uses constant-time comparison to prevent timing attacks
    - bcrypt.checkpw handles salt extraction automatically
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        bool: True if password matches
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Return False on any error to prevent information leakage
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        str: URL-safe base64 encoded token
    """
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """
    Hash a token for storage (e.g., refresh tokens, reset tokens).
    
    Uses SHA-256 for fast lookup while maintaining security.
    
    Args:
        token: Plain text token
        
    Returns:
        str: Hashed token
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generate_api_key() -> Tuple[str, str]:
    """
    Generate an API key pair (key and hash).
    
    Returns:
        Tuple[str, str]: (plain_key, hashed_key)
    """
    key = f"rpg_{secrets.token_urlsafe(32)}"
    hashed = hash_token(key)
    return key, hashed
