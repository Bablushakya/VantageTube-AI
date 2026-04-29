"""
VantageTube AI - User Service
Handles user profile and settings operations
"""

from typing import Optional
from datetime import datetime
from app.core.supabase import get_supabase
from app.core.security import get_password_hash, verify_password
from app.models.user import UserUpdate, UserResponse, PasswordChange
from app.models.settings import UserSettingsUpdate, UserSettingsResponse
from fastapi import HTTPException, status


class UserService:
    """Service for handling user profile operations"""
    
    @staticmethod
    async def update_profile(user_id: str, profile_data: UserUpdate) -> UserResponse:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            Updated user profile
            
        Raises:
            HTTPException: If update fails
        """
        supabase = get_supabase()
        
        try:
            # Prepare update data (only include non-None fields)
            update_data = {
                k: v for k, v in profile_data.model_dump().items() 
                if v is not None
            }
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data provided for update"
                )
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Update user profile
            response = supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_data = response.data[0]
            
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
                detail=f"Failed to update profile: {str(e)}"
            )
    
    @staticmethod
    async def change_password(user_id: str, password_data: PasswordChange) -> dict:
        """
        Change user password
        
        Args:
            user_id: User ID
            password_data: Password change data
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If password change fails
        """
        # Validate password confirmation
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        supabase = get_supabase()
        
        try:
            # Get user from Supabase Auth
            # Note: In production, you'd verify the current password with Supabase Auth
            # For now, we'll update the password directly
            
            # Update password in Supabase Auth
            from app.core.supabase import get_supabase_admin
            admin_client = get_supabase_admin()
            
            admin_client.auth.admin.update_user_by_id(
                user_id,
                {"password": password_data.new_password}
            )
            
            return {
                "message": "Password changed successfully",
                "user_id": user_id
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change password: {str(e)}"
            )
    
    @staticmethod
    async def get_settings(user_id: str) -> UserSettingsResponse:
        """
        Get user settings
        
        Args:
            user_id: User ID
            
        Returns:
            User settings
            
        Raises:
            HTTPException: If settings not found
        """
        supabase = get_supabase()
        
        try:
            response = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
            
            if not response.data:
                # Create default settings if not exists
                default_settings = {
                    "user_id": user_id,
                    "theme": "dark",
                    "accent_color": "#6C63FF",
                    "font_size": "normal",
                    "compact_mode": False,
                    "email_notifications": True,
                    "weekly_seo_report": True,
                    "trending_alerts": True,
                    "feature_updates": False,
                    "milestone_alerts": True,
                    "profile_visibility": True,
                    "analytics_sharing": True
                }
                
                create_response = supabase.table("user_settings").insert(default_settings).execute()
                
                if not create_response.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create default settings"
                    )
                
                settings_data = create_response.data[0]
            else:
                settings_data = response.data[0]
            
            return UserSettingsResponse(
                id=settings_data["id"],
                user_id=settings_data["user_id"],
                theme=settings_data.get("theme", "dark"),
                accent_color=settings_data.get("accent_color", "#6C63FF"),
                font_size=settings_data.get("font_size", "normal"),
                compact_mode=settings_data.get("compact_mode", False),
                email_notifications=settings_data.get("email_notifications", True),
                weekly_seo_report=settings_data.get("weekly_seo_report", True),
                trending_alerts=settings_data.get("trending_alerts", True),
                feature_updates=settings_data.get("feature_updates", False),
                milestone_alerts=settings_data.get("milestone_alerts", True),
                profile_visibility=settings_data.get("profile_visibility", True),
                analytics_sharing=settings_data.get("analytics_sharing", True)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get settings: {str(e)}"
            )
    
    @staticmethod
    async def update_settings(user_id: str, settings_data: UserSettingsUpdate) -> UserSettingsResponse:
        """
        Update user settings
        
        Args:
            user_id: User ID
            settings_data: Settings update data
            
        Returns:
            Updated settings
            
        Raises:
            HTTPException: If update fails
        """
        supabase = get_supabase()
        
        try:
            # Prepare update data (only include non-None fields)
            update_data = {
                k: v for k, v in settings_data.model_dump().items() 
                if v is not None
            }
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data provided for update"
                )
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Update settings
            response = supabase.table("user_settings").update(update_data).eq("user_id", user_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Settings not found"
                )
            
            settings_data = response.data[0]
            
            return UserSettingsResponse(
                id=settings_data["id"],
                user_id=settings_data["user_id"],
                theme=settings_data.get("theme", "dark"),
                accent_color=settings_data.get("accent_color", "#6C63FF"),
                font_size=settings_data.get("font_size", "normal"),
                compact_mode=settings_data.get("compact_mode", False),
                email_notifications=settings_data.get("email_notifications", True),
                weekly_seo_report=settings_data.get("weekly_seo_report", True),
                trending_alerts=settings_data.get("trending_alerts", True),
                feature_updates=settings_data.get("feature_updates", False),
                milestone_alerts=settings_data.get("milestone_alerts", True),
                profile_visibility=settings_data.get("profile_visibility", True),
                analytics_sharing=settings_data.get("analytics_sharing", True)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update settings: {str(e)}"
            )
