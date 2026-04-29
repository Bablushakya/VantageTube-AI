"""
VantageTube AI - User API Routes
Handles user profile and settings endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.models.user import UserUpdate, UserResponse, PasswordChange
from app.models.settings import UserSettingsUpdate, UserSettingsResponse
from app.services.user_service import UserService
from app.services.storage_service import StorageService
from app.api.auth import get_current_user_id


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user_id: str = Depends(get_current_user_id)):
    """
    Get current user profile
    
    Same as /auth/me but under /users for consistency
    """
    from app.services.auth_service import AuthService
    return await AuthService.get_current_user(user_id)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update current user profile
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **display_name**: Display name
    - **username**: Unique username
    - **country**: Country code (e.g., 'us', 'uk')
    - **niche**: Content niche (e.g., 'tech', 'gaming')
    - **bio**: User biography
    
    All fields are optional - only provided fields will be updated
    """
    return await UserService.update_profile(user_id, profile_data)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    user_id: str = Depends(get_current_user_id)
):
    """
    Change user password
    
    - **current_password**: Current password (for verification)
    - **new_password**: New password (minimum 8 characters)
    - **confirm_password**: Must match new password
    
    Returns success message if password changed successfully
    """
    return await UserService.change_password(user_id, password_data)


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload user avatar
    
    - **file**: Image file (JPG, PNG, GIF, WebP)
    - Maximum size: 5MB
    
    Returns public URL of uploaded avatar
    """
    avatar_url = await StorageService.upload_avatar(user_id, file)
    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }


@router.delete("/avatar")
async def delete_avatar(user_id: str = Depends(get_current_user_id)):
    """
    Delete user avatar
    
    Removes avatar from storage and sets avatar_url to null
    """
    # Get current user to get avatar URL
    from app.services.auth_service import AuthService
    user = await AuthService.get_current_user(user_id)
    
    if not user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete"
        )
    
    return await StorageService.delete_avatar(user_id, user.avatar_url)


@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(user_id: str = Depends(get_current_user_id)):
    """
    Get user settings
    
    Returns all user preferences and settings.
    Creates default settings if not exists.
    """
    return await UserService.get_settings(user_id)


@router.put("/settings", response_model=UserSettingsResponse)
async def update_settings(
    settings_data: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update user settings
    
    **Appearance:**
    - **theme**: 'dark' or 'light'
    - **accent_color**: Hex color code (e.g., '#6C63FF')
    - **font_size**: 'small', 'normal', or 'large'
    - **compact_mode**: Boolean
    
    **Notifications:**
    - **email_notifications**: Boolean
    - **weekly_seo_report**: Boolean
    - **trending_alerts**: Boolean
    - **feature_updates**: Boolean
    - **milestone_alerts**: Boolean
    
    **Privacy:**
    - **profile_visibility**: Boolean
    - **analytics_sharing**: Boolean
    
    All fields are optional - only provided fields will be updated
    """
    return await UserService.update_settings(user_id, settings_data)
