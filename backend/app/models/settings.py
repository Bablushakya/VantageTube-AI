"""
VantageTube AI - User Settings Models
Pydantic models for user settings data validation
"""

from pydantic import BaseModel
from typing import Optional


class UserSettingsBase(BaseModel):
    """Base settings model"""
    theme: Optional[str] = "dark"
    accent_color: Optional[str] = "#6C63FF"
    font_size: Optional[str] = "normal"
    compact_mode: Optional[bool] = False
    email_notifications: Optional[bool] = True
    weekly_seo_report: Optional[bool] = True
    trending_alerts: Optional[bool] = True
    feature_updates: Optional[bool] = False
    milestone_alerts: Optional[bool] = True
    profile_visibility: Optional[bool] = True
    analytics_sharing: Optional[bool] = True


class UserSettingsCreate(UserSettingsBase):
    """Model for creating user settings"""
    user_id: str


class UserSettingsUpdate(UserSettingsBase):
    """Model for updating user settings (all fields optional)"""
    pass


class UserSettingsResponse(UserSettingsBase):
    """Model for user settings response"""
    id: str
    user_id: str
    
    class Config:
        from_attributes = True
