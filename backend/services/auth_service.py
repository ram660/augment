"""
Authentication Service for HomeView AI.

Production-ready authentication with JWT tokens, password hashing,
and user management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    email: str
    user_type: str
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    """User login request."""
    email: str
    password: str


class UserRegister(BaseModel):
    """User registration request."""
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    user_type: str = Field(..., pattern="^(homeowner|contractor|diy_worker)$")


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    user_type: str
    created_at: datetime
    is_active: bool = True


class AuthService:
    """
    Production-ready authentication service.
    
    Features:
    - JWT token generation and validation
    - Password hashing with bcrypt
    - User registration and login
    - Token refresh
    - Role-based access control
    """
    
    def __init__(self, secret_key: str = SECRET_KEY):
        """
        Initialize auth service.
        
        Args:
            secret_key: Secret key for JWT encoding
        """
        self.secret_key = secret_key
        self.algorithm = ALGORITHM
        self.access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        logger.info("Auth service initialized")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        user_type: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User ID
            email: User email
            user_type: User type (homeowner, contractor, diy_worker)
            expires_delta: Optional custom expiration
            
        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.access_token_expire
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "user_type": user_type,
            "exp": expire,
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        user_type: str
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user_id: User ID
            email: User email
            user_type: User type
            
        Returns:
            JWT refresh token string
        """
        expire = datetime.utcnow() + self.refresh_token_expire
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "user_type": user_type,
            "exp": expire,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_tokens(
        self,
        user_id: str,
        email: str,
        user_type: str
    ) -> Token:
        """
        Create both access and refresh tokens.
        
        Args:
            user_id: User ID
            email: User email
            user_type: User type
            
        Returns:
            Token object with both tokens
        """
        access_token = self.create_access_token(user_id, email, user_type)
        refresh_token = self.create_refresh_token(user_id, email, user_type)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
        )
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            user_type: str = payload.get("user_type")
            exp: datetime = datetime.fromtimestamp(payload.get("exp"))
            
            if user_id is None or email is None:
                return None
            
            return TokenData(
                user_id=user_id,
                email=email,
                user_type=user_type,
                exp=exp
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh token is valid
        """
        token_data = self.verify_token(refresh_token)
        
        if not token_data:
            return None
        
        # Verify it's a refresh token
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                return None
        except jwt.JWTError:
            return None
        
        # Create new access token
        return self.create_access_token(
            user_id=token_data.user_id,
            email=token_data.email,
            user_type=token_data.user_type
        )
    
    def validate_user_type(self, token_data: TokenData, allowed_types: list[str]) -> bool:
        """
        Validate user type for role-based access control.
        
        Args:
            token_data: Token data
            allowed_types: List of allowed user types
            
        Returns:
            True if user type is allowed
        """
        return token_data.user_type in allowed_types

