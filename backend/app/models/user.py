"""
VantageTube AI - User Models
Pydantic models for user-related data validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None


class UserCreate(UserBase):
    """Model for user registration"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirm_password: str


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    username: Optional[str] = None
    country: Optional[str] = None
    niche: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(UserBase):
    """Model for user response (without sensitive data)"""
    id: str
    username: Optional[str] = None
    country: Optional[str] = None
    niche: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: str = "free"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Compute full name from first and last name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.display_name or self.email.split("@")[0]
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Model for decoded token data"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class PasswordChange(BaseModel):
    """Model for password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
