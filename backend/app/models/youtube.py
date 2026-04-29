"""
VantageTube AI - YouTube Models
Pydantic models for YouTube data validation
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class YouTubeChannelBase(BaseModel):
    """Base YouTube channel model"""
    channel_id: str
    channel_name: str
    channel_handle: Optional[str] = None
    channel_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[int] = 0
    video_count: Optional[int] = 0
    view_count: Optional[int] = 0
    description: Optional[str] = None


class YouTubeChannelCreate(YouTubeChannelBase):
    """Model for creating YouTube channel"""
    user_id: str
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_token_expires_at: datetime


class YouTubeChannelUpdate(BaseModel):
    """Model for updating YouTube channel"""
    channel_name: Optional[str] = None
    channel_handle: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    description: Optional[str] = None
    is_connected: Optional[bool] = None


class YouTubeChannelResponse(YouTubeChannelBase):
    """Model for YouTube channel response"""
    id: str
    user_id: str
    is_connected: bool
    connected_at: datetime
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    """Base video model"""
    video_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    view_count: Optional[int] = 0
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    published_at: Optional[datetime] = None
    tags: Optional[List[str]] = []
    category_id: Optional[str] = None


class VideoCreate(VideoBase):
    """Model for creating video"""
    user_id: str
    channel_id: str


class VideoUpdate(BaseModel):
    """Model for updating video"""
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    tags: Optional[List[str]] = None
    seo_score: Optional[int] = None


class VideoResponse(VideoBase):
    """Model for video response"""
    id: str
    user_id: str
    channel_id: str
    seo_score: Optional[int] = None
    last_analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OAuthCallbackData(BaseModel):
    """Model for OAuth callback data"""
    code: str
    state: Optional[str] = None


class ChannelSyncResponse(BaseModel):
    """Model for channel sync response"""
    channel: YouTubeChannelResponse
    videos_synced: int
    message: str
