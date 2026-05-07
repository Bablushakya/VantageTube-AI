"""
VantageTube AI - YouTube API Routes
Handles YouTube OAuth and channel management endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
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
async def youtube_oauth_authorize(user_id: str = Query(None)):
    """
    Initiate YouTube OAuth flow
    
    Redirects user to Google OAuth consent screen.
    After authorization, user will be redirected back to the callback URL.
    
    Can be called with:
    - user_id query parameter (for direct redirects from frontend)
    - Authorization header (for authenticated requests)
    
    Returns redirect to Google OAuth URL
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID required as query parameter"
        )
    
    auth_url = YouTubeService.get_oauth_url(user_id)
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
async def youtube_oauth_callback(
    code: str = Query(None, description="Authorization code from Google"),
    state: str = Query(None, description="User ID passed in state parameter"),
    error: str = Query(None, description="Error from Google OAuth")
):
    """
    Handle YouTube OAuth callback
    
    This endpoint is called by Google after user authorizes the app.
    It exchanges the authorization code for access tokens and fetches channel data.
    
    - **code**: Authorization code from Google
    - **state**: User ID (passed during authorization)
    - **error**: Error from Google (if authorization failed)
    
    Redirects to oauth-callback.html page with code and state parameters
    """
    try:
        # Check for OAuth errors
        if error:
            error_description = Query(None, description="Error description from Google")
            return RedirectResponse(
                url=f"/pages/oauth-callback.html?error={error}&error_description={error_description}",
                status_code=302
            )
        
        if not code or not state:
            return RedirectResponse(
                url="/pages/oauth-callback.html?error=missing_parameters",
                status_code=302
            )
        
        # Redirect to oauth-callback.html with code and state
        # The frontend will handle the token exchange
        return RedirectResponse(
            url=f"/pages/oauth-callback.html?code={code}&state={state}",
            status_code=302
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"/pages/oauth-callback.html?error=callback_failed&error_description={str(e)}",
            status_code=302
        )


@router.post("/oauth/exchange")
async def exchange_oauth_code(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID")
):
    """
    Exchange OAuth code for tokens and connect YouTube channel
    
    Called by frontend after OAuth callback
    
    - **code**: Authorization code from Google
    - **state**: User ID
    
    Returns connected YouTube channel data
    """
    try:
        channel = await YouTubeService.handle_oauth_callback(code, state)
        
        return {
            "success": True,
            "message": "YouTube channel connected successfully!",
            "channel": channel
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


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
    max_results: int = Query(200, ge=1, le=500, description="Maximum number of videos to sync (default 200, max 500)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Sync videos from YouTube channel.

    Fetches ALL videos via the uploads playlist (cheap: 1 quota unit per page),
    then writes them all in a single batch upsert.

    - **channel_id**: Channel database ID (not YouTube channel ID)
    - **max_results**: Maximum videos to fetch (1-500, default 200)
    """
    return await YouTubeService.sync_channel_videos(channel_id, user_id, max_results)


@router.get("/channels/{channel_id}/videos", response_model=List[VideoResponse])
async def get_channel_videos(
    channel_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of videos to return"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get videos for a channel from the database.

    Returns videos ordered by published date (newest first).

    - **channel_id**: Channel database ID
    - **limit**: Max videos to return (1-500, default 100)
    """
    return await YouTubeService.get_channel_videos(channel_id, user_id, limit)


@router.delete("/channels/{channel_id}")
async def disconnect_channel(
    channel_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Disconnect YouTube channel
    
    Deletes the channel connection and all associated data.
    
    - **channel_id**: Channel database ID
    
    Returns success message
    """
    from app.core.supabase import get_supabase
    supabase = get_supabase()
    
    try:
        # First, verify the channel belongs to the user
        channel_response = supabase.table("youtube_channels").select("*").eq("id", channel_id).eq("user_id", user_id).execute()
        
        if not channel_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        # Delete all videos associated with this channel
        supabase.table("videos").delete().eq("channel_id", channel_id).execute()
        
        # Delete the channel itself
        delete_response = supabase.table("youtube_channels").delete().eq("id", channel_id).eq("user_id", user_id).execute()
        
        if not delete_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disconnect channel"
            )
        
        return {
            "success": True,
            "message": "Channel disconnected successfully",
            "channel_id": channel_id
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect channel: {str(e)}"
        )
