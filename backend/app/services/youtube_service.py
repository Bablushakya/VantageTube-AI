"""
VantageTube AI - YouTube Service
Handles YouTube API integration and OAuth flow
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from app.core.config import settings
from app.core.supabase import get_supabase
from app.models.youtube import (
    YouTubeChannelResponse,
    VideoResponse,
    ChannelSyncResponse
)
from fastapi import HTTPException, status
import isodate


class YouTubeService:
    """Service for YouTube API operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]
    
    @staticmethod
    def get_oauth_url(user_id: str) -> str:
        """
        Generate YouTube OAuth authorization URL
        
        Args:
            user_id: User ID to include in state
            
        Returns:
            Authorization URL
        """
        if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="YouTube OAuth not configured. Please set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET"
            )
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
                }
            },
            scopes=YouTubeService.SCOPES,
            redirect_uri=settings.YOUTUBE_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=user_id,
            prompt='consent'
        )
        
        return authorization_url
    
    @staticmethod
    async def handle_oauth_callback(code: str, user_id: str) -> YouTubeChannelResponse:
        """
        Handle OAuth callback and fetch channel data
        
        Args:
            code: Authorization code from OAuth callback
            user_id: User ID
            
        Returns:
            Connected YouTube channel data
        """
        if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="YouTube OAuth not configured"
            )
        
        try:
            # Exchange code for tokens
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.YOUTUBE_CLIENT_ID,
                        "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
                    }
                },
                scopes=YouTubeService.SCOPES,
                redirect_uri=settings.YOUTUBE_REDIRECT_URI
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Build YouTube API client
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Fetch channel data
            channels_response = youtube.channels().list(
                part='snippet,statistics,contentDetails',
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No YouTube channel found for this account"
                )
            
            channel_data = channels_response['items'][0]
            
            # Prepare channel data for database
            channel_info = {
                "user_id": user_id,
                "channel_id": channel_data['id'],
                "channel_name": channel_data['snippet']['title'],
                "channel_handle": channel_data['snippet'].get('customUrl', ''),
                "channel_url": f"https://youtube.com/channel/{channel_data['id']}",
                "thumbnail_url": channel_data['snippet']['thumbnails']['high']['url'],
                "subscriber_count": int(channel_data['statistics'].get('subscriberCount', 0)),
                "video_count": int(channel_data['statistics'].get('videoCount', 0)),
                "view_count": int(channel_data['statistics'].get('viewCount', 0)),
                "description": channel_data['snippet'].get('description', ''),
                "published_at": channel_data['snippet']['publishedAt'],
                "oauth_access_token": credentials.token,
                "oauth_refresh_token": credentials.refresh_token,
                "oauth_token_expires_at": (datetime.utcnow() + timedelta(seconds=3600)).isoformat(),
                "is_connected": True,
                "connected_at": datetime.utcnow().isoformat(),
                "last_synced_at": datetime.utcnow().isoformat()
            }
            
            supabase = get_supabase()
            
            # Check if channel already exists
            existing = supabase.table("youtube_channels").select("*").eq("channel_id", channel_info["channel_id"]).execute()
            
            if existing.data:
                # Update existing channel
                response = supabase.table("youtube_channels").update(channel_info).eq("channel_id", channel_info["channel_id"]).execute()
            else:
                # Insert new channel
                response = supabase.table("youtube_channels").insert(channel_info).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save channel data"
                )
            
            saved_channel = response.data[0]
            
            return YouTubeChannelResponse(
                id=saved_channel["id"],
                user_id=saved_channel["user_id"],
                channel_id=saved_channel["channel_id"],
                channel_name=saved_channel["channel_name"],
                channel_handle=saved_channel.get("channel_handle"),
                channel_url=saved_channel.get("channel_url"),
                thumbnail_url=saved_channel.get("thumbnail_url"),
                subscriber_count=saved_channel.get("subscriber_count", 0),
                video_count=saved_channel.get("video_count", 0),
                view_count=saved_channel.get("view_count", 0),
                description=saved_channel.get("description"),
                is_connected=saved_channel.get("is_connected", True),
                connected_at=datetime.fromisoformat(saved_channel["connected_at"]),
                last_synced_at=datetime.fromisoformat(saved_channel["last_synced_at"]) if saved_channel.get("last_synced_at") else None,
                created_at=datetime.fromisoformat(saved_channel["created_at"])
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth callback failed: {str(e)}"
            )
    
    @staticmethod
    async def get_user_channels(user_id: str) -> List[YouTubeChannelResponse]:
        """
        Get all YouTube channels for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of YouTube channels
        """
        supabase = get_supabase()
        
        try:
            response = supabase.table("youtube_channels").select("*").eq("user_id", user_id).execute()
            
            channels = []
            for channel_data in response.data:
                channels.append(YouTubeChannelResponse(
                    id=channel_data["id"],
                    user_id=channel_data["user_id"],
                    channel_id=channel_data["channel_id"],
                    channel_name=channel_data["channel_name"],
                    channel_handle=channel_data.get("channel_handle"),
                    channel_url=channel_data.get("channel_url"),
                    thumbnail_url=channel_data.get("thumbnail_url"),
                    subscriber_count=channel_data.get("subscriber_count", 0),
                    video_count=channel_data.get("video_count", 0),
                    view_count=channel_data.get("view_count", 0),
                    description=channel_data.get("description"),
                    is_connected=channel_data.get("is_connected", True),
                    connected_at=datetime.fromisoformat(channel_data["connected_at"]),
                    last_synced_at=datetime.fromisoformat(channel_data["last_synced_at"]) if channel_data.get("last_synced_at") else None,
                    created_at=datetime.fromisoformat(channel_data["created_at"])
                ))
            
            return channels
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get channels: {str(e)}"
            )
    
    @staticmethod
    async def sync_channel_videos(channel_db_id: str, user_id: str, max_results: int = 50) -> ChannelSyncResponse:
        """
        Sync videos from YouTube channel
        
        Args:
            channel_db_id: Channel database ID
            user_id: User ID
            max_results: Maximum number of videos to fetch
            
        Returns:
            Sync response with channel and video count
        """
        supabase = get_supabase()
        
        try:
            # Get channel from database
            channel_response = supabase.table("youtube_channels").select("*").eq("id", channel_db_id).eq("user_id", user_id).execute()
            
            if not channel_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Channel not found"
                )
            
            channel_data = channel_response.data[0]
            
            # Build credentials
            credentials = Credentials(
                token=channel_data["oauth_access_token"],
                refresh_token=channel_data["oauth_refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET
            )
            
            # Build YouTube API client
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Fetch videos
            videos_response = youtube.search().list(
                part='id',
                channelId=channel_data["channel_id"],
                maxResults=max_results,
                order='date',
                type='video'
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in videos_response.get('items', [])]
            
            if not video_ids:
                return ChannelSyncResponse(
                    channel=YouTubeChannelResponse(**channel_data),
                    videos_synced=0,
                    message="No videos found"
                )
            
            # Fetch video details
            videos_details = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            videos_synced = 0
            
            for video in videos_details.get('items', []):
                # Parse duration
                duration_iso = video['contentDetails']['duration']
                duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
                
                video_info = {
                    "user_id": user_id,
                    "channel_id": channel_db_id,
                    "video_id": video['id'],
                    "title": video['snippet']['title'],
                    "description": video['snippet'].get('description', ''),
                    "thumbnail_url": video['snippet']['thumbnails']['high']['url'],
                    "duration": duration_seconds,
                    "view_count": int(video['statistics'].get('viewCount', 0)),
                    "like_count": int(video['statistics'].get('likeCount', 0)),
                    "comment_count": int(video['statistics'].get('commentCount', 0)),
                    "published_at": video['snippet']['publishedAt'],
                    "tags": video['snippet'].get('tags', []),
                    "category_id": video['snippet'].get('categoryId', '')
                }
                
                # Check if video exists
                existing_video = supabase.table("videos").select("*").eq("video_id", video_info["video_id"]).execute()
                
                if existing_video.data:
                    # Update existing video
                    supabase.table("videos").update(video_info).eq("video_id", video_info["video_id"]).execute()
                else:
                    # Insert new video
                    supabase.table("videos").insert(video_info).execute()
                
                videos_synced += 1
            
            # Update last_synced_at
            supabase.table("youtube_channels").update({
                "last_synced_at": datetime.utcnow().isoformat()
            }).eq("id", channel_db_id).execute()
            
            return ChannelSyncResponse(
                channel=YouTubeChannelResponse(
                    id=channel_data["id"],
                    user_id=channel_data["user_id"],
                    channel_id=channel_data["channel_id"],
                    channel_name=channel_data["channel_name"],
                    channel_handle=channel_data.get("channel_handle"),
                    channel_url=channel_data.get("channel_url"),
                    thumbnail_url=channel_data.get("thumbnail_url"),
                    subscriber_count=channel_data.get("subscriber_count", 0),
                    video_count=channel_data.get("video_count", 0),
                    view_count=channel_data.get("view_count", 0),
                    description=channel_data.get("description"),
                    is_connected=channel_data.get("is_connected", True),
                    connected_at=datetime.fromisoformat(channel_data["connected_at"]),
                    last_synced_at=datetime.utcnow(),
                    created_at=datetime.fromisoformat(channel_data["created_at"])
                ),
                videos_synced=videos_synced,
                message=f"Successfully synced {videos_synced} videos"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to sync videos: {str(e)}"
            )
    
    @staticmethod
    async def get_channel_videos(channel_db_id: str, user_id: str) -> List[VideoResponse]:
        """
        Get all videos for a channel
        
        Args:
            channel_db_id: Channel database ID
            user_id: User ID
            
        Returns:
            List of videos
        """
        supabase = get_supabase()
        
        try:
            response = supabase.table("videos").select("*").eq("channel_id", channel_db_id).eq("user_id", user_id).order("published_at", desc=True).execute()
            
            videos = []
            for video_data in response.data:
                videos.append(VideoResponse(
                    id=video_data["id"],
                    user_id=video_data["user_id"],
                    channel_id=video_data["channel_id"],
                    video_id=video_data["video_id"],
                    title=video_data["title"],
                    description=video_data.get("description"),
                    thumbnail_url=video_data.get("thumbnail_url"),
                    duration=video_data.get("duration"),
                    view_count=video_data.get("view_count", 0),
                    like_count=video_data.get("like_count", 0),
                    comment_count=video_data.get("comment_count", 0),
                    published_at=datetime.fromisoformat(video_data["published_at"]) if video_data.get("published_at") else None,
                    tags=video_data.get("tags", []),
                    category_id=video_data.get("category_id"),
                    seo_score=video_data.get("seo_score"),
                    last_analyzed_at=datetime.fromisoformat(video_data["last_analyzed_at"]) if video_data.get("last_analyzed_at") else None,
                    created_at=datetime.fromisoformat(video_data["created_at"]),
                    updated_at=datetime.fromisoformat(video_data["updated_at"]) if video_data.get("updated_at") else None
                ))
            
            return videos
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get videos: {str(e)}"
            )
