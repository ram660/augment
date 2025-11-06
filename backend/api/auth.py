"""
Authentication API endpoints for HomeView AI.

Provides user registration, login, token refresh, and user management.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.auth_service import (
    AuthService,
    UserLogin,
    UserRegister,
    UserResponse,
    Token,
    TokenData
)
from backend.models.user import User
from backend.models.base import get_async_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Security
security = HTTPBearer()

# Auth service instance
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    token_data = auth_service.verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    from uuid import UUID
    user_id = UUID(token_data.user_id) if isinstance(token_data.user_id, str) else token_data.user_id
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


def require_user_type(*allowed_types: str):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_types: Allowed user types
        
    Returns:
        Dependency function
    """
    async def check_user_type(current_user: User = Depends(get_current_user)) -> User:
        if current_user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required user type: {', '.join(allowed_types)}"
            )
        return current_user
    
    return check_user_type


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If email already exists
    """
    try:
        # Check if user already exists
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = auth_service.hash_password(user_data.password)
        
        # Create user
        user = User(
            id=str(uuid4()),
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            user_type=user_data.user_type,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User registered: {user.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            user_type=user.user_type,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login user and return JWT tokens.
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Get user by email
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not auth_service.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create tokens
        tokens = auth_service.create_tokens(
            user_id=str(user.id),
            email=user.email,
            user_type=user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type)
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str = Header(..., alias="X-Refresh-Token")
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    new_access_token = auth_service.refresh_access_token(refresh_token)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        user_type=current_user.user_type.value if hasattr(current_user.user_type, 'value') else str(current_user.user_type),
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user (client should discard tokens).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.email}")
    
    return {
        "message": "Successfully logged out",
        "detail": "Please discard your tokens"
    }

