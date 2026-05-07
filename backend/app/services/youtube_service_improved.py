"""
VantageTube AI - YouTube Service (Improved Sync)
Handles YouTube API integration with comprehensive error handling and logging
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.core.config import settings
from app.core.supabase import get_supabase, get_supabase_admin
from app.models.youtube import (
    YouTubeChannelResponse,
    VideoResponse,
    ChannelSyncResponse
)
from fastapi import HTTPException, status
import isodate

# Configure logging
logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for YouTube API operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]
    
    @staticmethod
    async def sync_channel_videos(
        channel_db_id: str,
        user_id: str,
        max_results: int = 50
    ) -> ChannelSyncResponse:
        """
        Sync videos from YouTube channel with comprehensive error handling
        
        Args:
            channel_db_id: Channel database ID
            user_id: User ID
            max_results: Maximum number of videos to fetch per request
            
        Returns:
            Sync response with channel and video count
            
        Raises:
            HTTPException: If sync fails
        """
        supabase = get_supabase()
        sync_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting sync for channel {channel_db_id}, user {user_id}")
            
            # ============================================================
            # STEP 1: Fetch channel from database
            # ============================================================
            logger.debug(f"Fetching channel {channel_db_id} from database")
            
            try:
                channel_response = supabase.table("youtube_channels").select("*").eq(
                    "id", channel_db_id
                ).eq("user_id", user_id).execute()
            except Exception as e:
                logger.error(f"Database error fetching channel: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: Failed to fetch channel from database"
                )
            
            if not channel_response.data:
                logger.warning(f"Channel {channel_db_id} not found for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Channel not found"
                )
            
            channel_data = channel_response.data[0]
            logger.info(f"Channel found: {channel_data.get('channel_name')}")
            
            # ============================================================
            # STEP 2: Build and validate credentials
            # ============================================================
            logger.debug("Building OAuth credentials")
            
            try:
                # Check if token is expired
                token_expires_at = channel_data.get("oauth_token_expires_at")
                if token_expires_at:
                    expires_dt = datetime.fromisoformat(token_expires_at)
                    if datetime.utcnow() > expires_dt:
                        logger.warning("OAuth token expired, attempting refresh")
                
                credentials = Credentials(
                    token=channel_data.get("oauth_access_token"),
                    refresh_token=channel_data.get("oauth_refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.YOUTUBE_CLIENT_ID,
                    client_secret=settings.YOUTUBE_CLIENT_SECRET
                )
                
                # Attempt to refresh if expired
                if credentials.expired and credentials.refresh_token:
                    logger.info("Refreshing expired OAuth token")
                    try:
                        request = Request()
                        credentials.refresh(request)
                        logger.info("Token refreshed successfully")
                        
                        # Update token in database
                        supabase.table("youtube_channels").update({
                            "oauth_access_token": credentials.token,
                            "oauth_token_expires_at": (
                                datetime.utcnow() + timedelta(hours=1)
                            ).isoformat()
                        }).eq("id", channel_db_id).execute()
                        logger.debug("Updated token in database")
                    except Exception as e:
                        logger.error(f"Failed to refresh token: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="OAuth token expired and refresh failed. Please reconnect your YouTube channel."
                        )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Credentials error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to build OAuth credentials"
                )
            
            # ============================================================
            # STEP 3: Build YouTube API client
            # ============================================================
            logger.debug("Building YouTube API client")
            
            try:
                youtube = build('youtube', 'v3', credentials=credentials)
                logger.debug("YouTube API client built successfully")
            except Exception as e:
                logger.error(f"YouTube API client error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to build YouTube API client"
                )
            
            # ============================================================
            # STEP 4: Fetch videos with pagination
            # ============================================================
            logger.info(f"Fetching videos from YouTube (max {max_results} per request)")
            
            all_video_ids = []
            next_page_token = None
            page_count = 0
            
            try:
                while len(all_video_ids) < max_results:
                    page_count += 1
                    logger.debug(f"Fetching page {page_count}")
                    
                    try:
                        videos_response = youtube.search().list(
                            part='id',
                            channelId=channel_data.get("channel_id"),
                            maxResults=min(50, max_results - len(all_video_ids)),
                            order='date',
                            type='video',
                            pageToken=next_page_token
                        ).execute()
                    except Exception as e:
                        logger.error(f"YouTube API search error on page {page_count}: {str(e)}")
                        if "quotaExceeded" in str(e):
                            raise HTTPException(
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="YouTube API quota exceeded. Please try again later."
                            )
                        elif "unauthorized" in str(e).lower():
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="YouTube API authorization failed. Please reconnect your channel."
                            )
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"YouTube API error: {str(e)}"
                            )
                    
                    items = videos_response.get('items', [])
                    logger.debug(f"Page {page_count}: Found {len(items)} videos")
                    
                    if not items:
                        logger.info(f"No more videos found after {page_count} pages")
                        break
                    
                    video_ids = [item['id']['videoId'] for item in items]
                    all_video_ids.extend(video_ids)
                    
                    next_page_token = videos_response.get('nextPageToken')
                    if not next_page_token:
                        logger.info(f"Reached end of videos after {page_count} pages")
                        break
                
                logger.info(f"Total videos found: {len(all_video_ids)}")
                
                if not all_video_ids:
                    logger.info("No videos found for channel")
                    return ChannelSyncResponse(
                        channel=YouTubeChannelResponse(**channel_data),
                        videos_synced=0,
                        message="No videos found"
                    )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error fetching video IDs: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch video list from YouTube"
                )
            
            # ============================================================
            # STEP 5: Fetch video details
            # ============================================================
            logger.info(f"Fetching details for {len(all_video_ids)} videos")
            
            videos_to_sync = []
            failed_videos = []
            
            try:
                # Fetch in batches (YouTube API limit is 50 per request)
                for i in range(0, len(all_video_ids), 50):
                    batch_ids = all_video_ids[i:i+50]
                    logger.debug(f"Fetching details for batch {i//50 + 1}")
                    
                    try:
                        videos_details = youtube.videos().list(
                            part='snippet,statistics,contentDetails',
                            id=','.join(batch_ids)
                        ).execute()
                    except Exception as e:
                        logger.error(f"YouTube API video details error: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to fetch video details from YouTube"
                        )
                    
                    for video in videos_details.get('items', []):
                        try:
                            # Parse duration
                            duration_iso = video.get('contentDetails', {}).get('duration', 'PT0S')
                            try:
                                duration_seconds = int(
                                    isodate.parse_duration(duration_iso).total_seconds()
                                )
                            except Exception as e:
                                logger.warning(f"Failed to parse duration {duration_iso}: {str(e)}")
                                duration_seconds = 0
                            
                            # Get thumbnail URL safely
                            thumbnails = video.get('snippet', {}).get('thumbnails', {})
                            thumbnail_url = (
                                thumbnails.get('high', {}).get('url') or
                                thumbnails.get('medium', {}).get('url') or
                                thumbnails.get('default', {}).get('url') or
                                None
                            )
                            
                            # Get statistics safely
                            statistics = video.get('statistics', {})
                            
                            video_info = {
                                "user_id": user_id,
                                "channel_id": channel_db_id,
                                "video_id": video.get('id'),
                                "title": video.get('snippet', {}).get('title', 'Untitled'),
                                "description": video.get('snippet', {}).get('description', ''),
                                "thumbnail_url": thumbnail_url,
                                "duration": duration_seconds,
                                "view_count": int(statistics.get('viewCount', 0)),
                                "like_count": int(statistics.get('likeCount', 0)),
                                "comment_count": int(statistics.get('commentCount', 0)),
                                "published_at": video.get('snippet', {}).get('publishedAt'),
                                "tags": video.get('snippet', {}).get('tags', []),
                                "category_id": video.get('snippet', {}).get('categoryId', '')
                            }
                            
                            videos_to_sync.append(video_info)
                            
                        except Exception as e:
                            logger.warning(f"Failed to parse video {video.get('id')}: {str(e)}")
                            failed_videos.append({
                                "video_id": video.get('id'),
                                "error": str(e)
                            })
                
                logger.info(f"Parsed {len(videos_to_sync)} videos successfully, {len(failed_videos)} failed")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error fetching video details: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch video details"
                )
            
            # ============================================================
            # STEP 6: Sync videos to database
            # ============================================================
            logger.info(f"Syncing {len(videos_to_sync)} videos to database")
            
            videos_synced = 0
            videos_updated = 0
            sync_errors = []
            
            try:
                for video_info in videos_to_sync:
                    try:
                        # Check if video exists
                        existing_video = supabase.table("videos").select("id").eq(
                            "video_id", video_info["video_id"]
                        ).execute()
                        
                        if existing_video.data:
                            # Update existing video
                            try:
                                supabase.table("videos").update(video_info).eq(
                                    "video_id", video_info["video_id"]
                                ).execute()
                                videos_updated += 1
                                logger.debug(f"Updated video {video_info['video_id']}")
                            except Exception as e:
                                logger.warning(f"Failed to update video {video_info['video_id']}: {str(e)}")
                                sync_errors.append({
                                    "video_id": video_info["video_id"],
                                    "operation": "update",
                                    "error": str(e)
                                })
                        else:
                            # Insert new video
                            try:
                                supabase.table("videos").insert(video_info).execute()
                                videos_synced += 1
                                logger.debug(f"Inserted video {video_info['video_id']}")
                            except Exception as e:
                                logger.warning(f"Failed to insert video {video_info['video_id']}: {str(e)}")
                                sync_errors.append({
                                    "video_id": video_info["video_id"],
                                    "operation": "insert",
                                    "error": str(e)
                                })
                    
                    except Exception as e:
                        logger.error(f"Error syncing video {video_info.get('video_id')}: {str(e)}")
                        sync_errors.append({
                            "video_id": video_info.get("video_id"),
                            "error": str(e)
                        })
                
                logger.info(f"Sync complete: {videos_synced} inserted, {videos_updated} updated, {len(sync_errors)} errors")
                
            except Exception as e:
                logger.error(f"Error during database sync: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to sync videos to database"
                )
            
            # ============================================================
            # STEP 7: Update channel last_synced_at
            # ============================================================
            logger.debug("Updating channel last_synced_at")
            
            try:
                supabase.table("youtube_channels").update({
                    "last_synced_at": datetime.utcnow().isoformat()
                }).eq("id", channel_db_id).execute()
                logger.debug("Updated channel last_synced_at")
            except Exception as e:
                logger.warning(f"Failed to update last_synced_at: {str(e)}")
                # Don't fail the entire sync for this
            
            # ============================================================
            # STEP 8: Return response
            # ============================================================
            sync_duration = (datetime.utcnow() - sync_start_time).total_seconds()
            logger.info(f"Sync completed in {sync_duration:.2f} seconds")
            
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
                videos_synced=videos_synced + videos_updated,
                message=f"Successfully synced {videos_synced + videos_updated} videos ({videos_synced} new, {videos_updated} updated)"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in sync_channel_videos: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during sync: {str(e)}"
            )
