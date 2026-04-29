"""
VantageTube AI - YouTube API Routes
Handles YouTube OAuth and channel management endpoints
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from typing import List
from app.models.youtube import (
    YouTubeChannelResponse,
    VideoResponse,
    ChannelSyncResponse,
    OAuthCallbackData
)
from app.services.youtube_service import YouTubeService
from app.api.auth import get_current_user_id


router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.get("/oauth/authorize")
async def youtube_oauth_authorize(user_id: str = Depends(get_current_user_id)):
    """
    Initiate YouTube OAuth flow
    
    Redirects user to Google OAuth consent screen.
    After authorization, user will be redirected back to the callback URL.
    
    Returns redirect to Google OAuth URL
    """
    auth_url = YouTubeService.get_oauth_url(user_id)
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
async def youtube_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID passed in state parameter")
):
    """
    Handle YouTube OAuth callback
    
    This endpoint is called by Google after user authorizes the app.
    It exchanges the authorization code for access tokens and fetches channel data.
    
    - **code**: Authorization code from Google
    - **state**: User ID (passed during authorization)
    
    Returns connected YouTube channel data
    """
    channel = await YouTubeService.handle_oauth_callback(code, state)
    
    # In production, redirect to frontend with success message
    # For now, return channel data
    return {
        "message": "YouTube channel connected successfully!",
        "channel": channel
    }


@router.get("/channels", response_model=List[YouTubeChannelResponse])
async def get_user_channels(user_id: str = Depends(get_current_user_id)):
    """
    Get all connected YouTube channels for current user
    
    Returns list of connected channels with statistics
    """
    return await YouTubeService.get_user_channels(user_id)


@router.post("/channels/{channel_id}/sync", response_model=ChannelSyncResponse)
async def sync_channel_videos(
    channel_id: str,
    max_results: int = Query(50, ge=1, le=50, description="Maximum number of videos to sync"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Sync videos from YouTube channel
    
    Fetches latest videos from YouTube and stores them in database.
    Updates existing videos if they already exist.
    
    - **channel_id**: Channel database ID (not YouTube channel ID)
    - **max_results**: Maximum number of videos to fetch (1-50)
    
    Returns sync result with number of videos synced
    """
    return await YouTubeService.sync_channel_videos(channel_id, user_id, max_results)


@router.get("/channels/{channel_id}/videos", response_model=List[VideoResponse])
async def get_channel_videos(
    channel_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all videos for a channel
    
    Returns list of videos from database (not from YouTube API).
    Videos are ordered by published date (newest first).
    
    - **channel_id**: Channel database ID
    
    Returns list of videos with statistics and SEO scores
    """
    return await YouTubeService.get_channel_videos(channel_id, user_id)


@router.delete("/channels/{channel_id}")
async def disconnect_channel(
    channel_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Disconnect YouTube channel
    
    Marks channel as disconnected but keeps historical data.
    
    - **channel_id**: Channel database ID
    
    Returns success message
    """
    from app.core.supabase import get_supabase
    supabase = get_supabase()
    
    # Update channel to disconnected
    response = supabase.table("youtube_channels").update({
        "is_connected": False
    }).eq("id", channel_id).eq("user_id", user_id).execute()
    
    if not response.data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    return {
        "message": "Channel disconnected successfully",
        "channel_id": channel_id
    }
