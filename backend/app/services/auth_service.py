"""
VantageTube AI - Authentication Service
Handles user registration, login, and authentication logic
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.core.supabase import get_supabase, get_supabase_admin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from fastapi import HTTPException, status


class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    async def register_user(user_data: UserCreate) -> Token:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            Token with user information
            
        Raises:
            HTTPException: If registration fails
        """
        # Validate password confirmation
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        supabase = get_supabase()
        admin_supabase = get_supabase_admin()  # Use admin client for user creation
        
        try:
            # Check if user already exists
            existing_user = admin_supabase.table("users").select("*").eq("email", user_data.email).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user in Supabase Auth (without email confirmation for now)
            try:
                auth_response = supabase.auth.sign_up({
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {
                        "email_redirect_to": None  # Disable email confirmation
                    }
                })
            except Exception as auth_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create auth account: {str(auth_error)}"
                )
            
            # Check if user was created
            if not auth_response or not hasattr(auth_response, 'user') or not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user account - no user returned"
                )
            
            user_id = auth_response.user.id
            
            # Create user profile in database
            user_profile = {
                "id": user_id,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "display_name": user_data.display_name or f"{user_data.first_name} {user_data.last_name}",
                "plan": "free",
                "created_at": datetime.utcnow().isoformat()
            }
            
            try:
                profile_response = admin_supabase.table("users").insert(user_profile).execute()
            except Exception as db_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create user profile: {str(db_error)}"
                )
            
            if not profile_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user profile - no data returned"
                )
            
            # Create tokens
            access_token = create_access_token({"sub": user_id, "email": user_data.email})
            refresh_token = create_refresh_token({"sub": user_id})
            
            # Prepare user response
            user_response = UserResponse(
                id=user_id,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_profile["display_name"],
                plan="free",
                created_at=datetime.utcnow()
            )
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(credentials: UserLogin) -> Token:
        """
        Authenticate user and return tokens
        
        Args:
            credentials: User login credentials
            
        Returns:
            Token with user information
            
        Raises:
            HTTPException: If authentication fails
        """
        supabase = get_supabase()
        admin_supabase = get_supabase_admin()
        
        try:
            # Authenticate with Supabase
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": credentials.email,
                    "password": credentials.password
                })
            except Exception as auth_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid email or password: {str(auth_error)}"
                )
            
            if not auth_response or not hasattr(auth_response, 'user') or not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            user_id = auth_response.user.id
            
            # Get user profile from database using admin client
            try:
                user_profile = admin_supabase.table("users").select("*").eq("id", user_id).execute()
            except Exception as db_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch user profile: {str(db_error)}"
                )
            
            if not user_profile.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            user_data = user_profile.data[0]
            
            # Create tokens
            access_token = create_access_token({"sub": user_id, "email": credentials.email})
            refresh_token = create_refresh_token({"sub": user_id})
            
            # Prepare user response
            user_response = UserResponse(
                id=user_data["id"],
                email=user_data["email"],
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                display_name=user_data.get("display_name"),
                username=user_data.get("username"),
                country=user_data.get("country"),
                niche=user_data.get("niche"),
                bio=user_data.get("bio"),
                avatar_url=user_data.get("avatar_url"),
                plan=user_data.get("plan", "free"),
                created_at=datetime.fromisoformat(user_data["created_at"]),
                updated_at=datetime.fromisoformat(user_data["updated_at"]) if user_data.get("updated_at") else None
            )
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
    
    @staticmethod
    async def get_current_user(user_id: str) -> UserResponse:
        """
        Get current user profile
        
        Args:
            user_id: User ID from JWT token
            
        Returns:
            User profile data
            
        Raises:
            HTTPException: If user not found
        """
        supabase = get_supabase()
        
        try:
            user_profile = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not user_profile.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_data = user_profile.data[0]
            
            return UserResponse(
                id=user_data["id"],
                email=user_data["email"],
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                display_name=user_data.get("display_name"),
                username=user_data.get("username"),
                country=user_data.get("country"),
                niche=user_data.get("niche"),
                bio=user_data.get("bio"),
                avatar_url=user_data.get("avatar_url"),
                plan=user_data.get("plan", "free"),
                created_at=datetime.fromisoformat(user_data["created_at"]),
                updated_at=datetime.fromisoformat(user_data["updated_at"]) if user_data.get("updated_at") else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )
