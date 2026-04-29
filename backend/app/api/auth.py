"""
VantageTube AI - Authentication API Routes
Handles user registration, login, and authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import UserCreate, UserLogin, UserResponse, Token, PasswordChange
from app.services.auth_service import AuthService
from app.core.security import decode_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle it


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to extract and validate user ID from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    # Check if credentials were provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Decode and validate token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **confirm_password**: Must match password
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional)
    - **display_name**: Display name (optional, defaults to first + last name)
    
    Returns JWT access token and user profile
    """
    return await AuthService.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return access token
    
    - **email**: Registered email address
    - **password**: User password
    
    Returns JWT access token and user profile
    """
    return await AuthService.login_user(credentials)


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user profile
    
    Requires valid JWT token in Authorization header
    """
    return await AuthService.get_current_user(user_id)


@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user_id)):
    """
    Logout current user
    
    Note: With JWT, logout is handled client-side by removing the token.
    This endpoint is provided for consistency and future server-side session management.
    """
    return {
        "message": "Logged out successfully",
        "user_id": user_id
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(user_id: str = Depends(get_current_user_id)):
    """
    Refresh access token using refresh token
    
    Requires valid JWT token in Authorization header
    """
    # In a production app, you'd validate the refresh token separately
    # For now, we'll just issue new tokens
    user = await AuthService.get_current_user(user_id)
    
    from app.core.security import create_access_token, create_refresh_token
    
    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.get("/check")
async def check_auth(user_id: str = Depends(get_current_user_id)):
    """
    Check if user is authenticated
    
    Returns user ID if token is valid
    """
    return {
        "authenticated": True,
        "user_id": user_id
    }
