"""
VantageTube AI - YouTube Service
Phase 4 improvements:
  4.1  Batch upsert  — all videos written in ONE DB call (was N×2 calls)
  4.2  Full pagination — fetches ALL videos, not just the first page of 50
  4.3  Token refresh  — checks expiry before building the API client;
                        refreshes automatically and persists new tokens
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone

import isodate
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.supabase import get_supabase, get_supabase_admin
from app.models.youtube import (
    YouTubeChannelResponse,
    VideoResponse,
    ChannelSyncResponse,
)

logger = logging.getLogger(__name__)

# YouTube Data API v3 costs 100 units per search.list call.
# videos.list costs 1 unit per call (up to 50 IDs per request).
# We use playlistItems.list (1 unit) instead of search.list (100 units)
# for pagination — much cheaper on quota.
_YT_PAGE_SIZE = 50          # max items per API page (YouTube hard limit)
_SYNC_MAX_VIDEOS = 500      # safety cap — prevents runaway syncs on huge channels


class YouTubeService:
    """Service for YouTube API operations."""

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # OAUTH HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _oauth_client_config() -> dict:
        return {
            "web": {
                "client_id":     settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
            }
        }

    @staticmethod
    def _require_oauth_config():
        if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="YouTube OAuth not configured. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET.",
            )

    @staticmethod
    def _parse_dt(raw: Optional[str]) -> Optional[datetime]:
        """Parse an ISO datetime string, returning None on failure."""
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def _channel_row_to_response(row: dict) -> YouTubeChannelResponse:
        return YouTubeChannelResponse(
            id=row["id"],
            user_id=row["user_id"],
            channel_id=row["channel_id"],
            channel_name=row["channel_name"],
            channel_handle=row.get("channel_handle"),
            channel_url=row.get("channel_url"),
            thumbnail_url=row.get("thumbnail_url"),
            subscriber_count=row.get("subscriber_count", 0),
            video_count=row.get("video_count", 0),
            view_count=row.get("view_count", 0),
            description=row.get("description"),
            is_connected=row.get("is_connected", True),
            connected_at=YouTubeService._parse_dt(row.get("connected_at")) or datetime.utcnow(),
            last_synced_at=YouTubeService._parse_dt(row.get("last_synced_at")),
            created_at=YouTubeService._parse_dt(row.get("created_at")) or datetime.utcnow(),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 4.3  TOKEN REFRESH
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_credentials(channel_data: dict) -> Credentials:
        """
        Build a Credentials object.  If the token is expired (or within
        60 seconds of expiry), refresh it automatically and persist the
        new token back to the database.
        """
        creds = Credentials(
            token=channel_data["oauth_access_token"],
            refresh_token=channel_data["oauth_refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.YOUTUBE_CLIENT_ID,
            client_secret=settings.YOUTUBE_CLIENT_SECRET,
        )

        # Check expiry
        expires_raw = channel_data.get("oauth_token_expires_at")
        if expires_raw:
            try:
                expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                # Make both timezone-aware for comparison
                now_utc = datetime.now(timezone.utc)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                token_is_stale = (expires_at - now_utc) < timedelta(seconds=60)
            except Exception:
                token_is_stale = True
        else:
            token_is_stale = True   # no expiry stored → assume stale

        if token_is_stale and creds.refresh_token:
            logger.info(f"Refreshing OAuth token for channel {channel_data['channel_id']}")
            try:
                creds.refresh(GoogleAuthRequest())
                # Persist refreshed token
                supabase = get_supabase_admin()
                supabase.table("youtube_channels").update({
                    "oauth_access_token":    creds.token,
                    "oauth_token_expires_at": (
                        datetime.now(timezone.utc) + timedelta(seconds=3600)
                    ).isoformat(),
                }).eq("id", channel_data["id"]).execute()
                logger.info("OAuth token refreshed and persisted")
            except Exception as exc:
                logger.warning(f"Token refresh failed: {exc} — proceeding with existing token")

        return creds

    # ─────────────────────────────────────────────────────────────────────────
    # OAUTH FLOW
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_oauth_url(user_id: str) -> str:
        YouTubeService._require_oauth_config()
        flow = Flow.from_client_config(
            YouTubeService._oauth_client_config(),
            scopes=YouTubeService.SCOPES,
            redirect_uri=settings.YOUTUBE_REDIRECT_URI,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=user_id,
            prompt="consent",
        )
        return auth_url

    @staticmethod
    async def handle_oauth_callback(code: str, user_id: str) -> YouTubeChannelResponse:
        YouTubeService._require_oauth_config()
        try:
            flow = Flow.from_client_config(
                YouTubeService._oauth_client_config(),
                scopes=YouTubeService.SCOPES,
                redirect_uri=settings.YOUTUBE_REDIRECT_URI,
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials

            youtube = build("youtube", "v3", credentials=credentials)
            channels_resp = youtube.channels().list(
                part="snippet,statistics,contentDetails", mine=True
            ).execute()

            if not channels_resp.get("items"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No YouTube channel found for this account",
                )

            ch = channels_resp["items"][0]
            thumbnails = ch["snippet"].get("thumbnails", {})
            thumb_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )

            channel_info = {
                "user_id":                user_id,
                "channel_id":             ch["id"],
                "channel_name":           ch["snippet"]["title"],
                "channel_handle":         ch["snippet"].get("customUrl", ""),
                "channel_url":            f"https://youtube.com/channel/{ch['id']}",
                "thumbnail_url":          thumb_url,
                "subscriber_count":       int(ch["statistics"].get("subscriberCount", 0)),
                "video_count":            int(ch["statistics"].get("videoCount", 0)),
                "view_count":             int(ch["statistics"].get("viewCount", 0)),
                "description":            ch["snippet"].get("description", ""),
                "published_at":           ch["snippet"]["publishedAt"],
                "oauth_access_token":     credentials.token,
                "oauth_refresh_token":    credentials.refresh_token,
                "oauth_token_expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=3600)
                ).isoformat(),
                "is_connected":           True,
                "connected_at":           datetime.utcnow().isoformat(),
                "last_synced_at":         datetime.utcnow().isoformat(),
            }

            supabase = get_supabase_admin()
            existing = (
                supabase.table("youtube_channels")
                .select("id")
                .eq("channel_id", channel_info["channel_id"])
                .execute()
            )
            if existing.data:
                resp = (
                    supabase.table("youtube_channels")
                    .update(channel_info)
                    .eq("channel_id", channel_info["channel_id"])
                    .execute()
                )
            else:
                resp = supabase.table("youtube_channels").insert(channel_info).execute()

            if not resp.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save channel data",
                )

            return YouTubeService._channel_row_to_response(resp.data[0])

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("OAuth callback failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth callback failed: {exc}",
            )

    # ─────────────────────────────────────────────────────────────────────────
    # CHANNEL QUERIES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_user_channels(user_id: str) -> List[YouTubeChannelResponse]:
        supabase = get_supabase()
        try:
            resp = (
                supabase.table("youtube_channels")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return [YouTubeService._channel_row_to_response(row) for row in resp.data]
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get channels: {exc}",
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 4.1 + 4.2  SYNC — batch upsert + full pagination
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def sync_channel_videos(
        channel_db_id: str,
        user_id: str,
        max_results: int = 200,
    ) -> ChannelSyncResponse:
        """
        Sync all videos from a YouTube channel.

        Improvements over the old implementation:
        - Uses playlistItems.list (1 quota unit) instead of search.list (100 units)
          for pagination — 100× cheaper on YouTube API quota.
        - Fetches ALL pages until the channel is exhausted or _SYNC_MAX_VIDEOS reached.
        - Collects all video dicts into a list, then writes them in ONE batch upsert
          instead of N×2 individual SELECT + INSERT/UPDATE calls.
        - Refreshes expired OAuth tokens before building the API client.
        """
        supabase = get_supabase()

        # ── 1. Load channel row ───────────────────────────────────────────────
        ch_resp = (
            supabase.table("youtube_channels")
            .select("*")
            .eq("id", channel_db_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not ch_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        channel_data = ch_resp.data[0]

        # ── 2. Build credentials (with auto-refresh) ──────────────────────────
        credentials = YouTubeService._build_credentials(channel_data)
        youtube = build("youtube", "v3", credentials=credentials)

        # ── 3. Get the channel's "uploads" playlist ID ────────────────────────
        # This is the cheapest way to enumerate all videos (1 unit per page).
        try:
            ch_detail = youtube.channels().list(
                part="contentDetails",
                id=channel_data["channel_id"],
            ).execute()
            uploads_playlist_id = (
                ch_detail["items"][0]["contentDetails"]
                ["relatedPlaylists"]["uploads"]
            )
        except Exception as exc:
            logger.error(f"Could not get uploads playlist: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get channel uploads playlist: {exc}",
            )

        # ── 4. Paginate through playlistItems to collect all video IDs ─────────
        video_ids: List[str] = []
        next_page_token: Optional[str] = None
        cap = min(max_results, _SYNC_MAX_VIDEOS)

        while len(video_ids) < cap:
            batch_size = min(_YT_PAGE_SIZE, cap - len(video_ids))
            kwargs = dict(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=batch_size,
            )
            if next_page_token:
                kwargs["pageToken"] = next_page_token

            try:
                page = youtube.playlistItems().list(**kwargs).execute()
            except Exception as exc:
                logger.error(f"playlistItems.list failed: {exc}")
                break

            for item in page.get("items", []):
                vid_id = item["contentDetails"].get("videoId")
                if vid_id:
                    video_ids.append(vid_id)

            next_page_token = page.get("nextPageToken")
            if not next_page_token:
                break   # no more pages

        if not video_ids:
            logger.info(f"No videos found for channel {channel_data['channel_id']}")
            return ChannelSyncResponse(
                channel=YouTubeService._channel_row_to_response(channel_data),
                videos_synced=0,
                message="No videos found in channel",
            )

        logger.info(f"Found {len(video_ids)} video IDs — fetching details…")

        # ── 5. Fetch video details in batches of 50 ───────────────────────────
        # videos.list accepts up to 50 IDs per call (1 quota unit each).
        video_rows: List[dict] = []

        for i in range(0, len(video_ids), _YT_PAGE_SIZE):
            batch_ids = video_ids[i : i + _YT_PAGE_SIZE]
            try:
                details = youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(batch_ids),
                ).execute()
            except Exception as exc:
                logger.warning(f"videos.list batch {i//50} failed: {exc} — skipping batch")
                continue

            for video in details.get("items", []):
                # Parse duration safely
                try:
                    duration_iso = video["contentDetails"]["duration"]
                    duration_secs = int(isodate.parse_duration(duration_iso).total_seconds())
                except Exception:
                    duration_secs = 0

                # Thumbnail — prefer high, fall back gracefully
                thumbs = video["snippet"].get("thumbnails", {})
                thumb_url = (
                    thumbs.get("high", {}).get("url")
                    or thumbs.get("medium", {}).get("url")
                    or thumbs.get("default", {}).get("url", "")
                )

                video_rows.append({
                    "user_id":       user_id,
                    "channel_id":    channel_db_id,
                    "video_id":      video["id"],
                    "title":         video["snippet"]["title"],
                    "description":   video["snippet"].get("description", ""),
                    "thumbnail_url": thumb_url,
                    "duration":      duration_secs,
                    "view_count":    int(video["statistics"].get("viewCount",    0)),
                    "like_count":    int(video["statistics"].get("likeCount",    0)),
                    "comment_count": int(video["statistics"].get("commentCount", 0)),
                    "published_at":  video["snippet"]["publishedAt"],
                    "tags":          video["snippet"].get("tags", []),
                    "category_id":   video["snippet"].get("categoryId", ""),
                })

        if not video_rows:
            return ChannelSyncResponse(
                channel=YouTubeService._channel_row_to_response(channel_data),
                videos_synced=0,
                message="Video details could not be fetched",
            )

        # ── 6. Batch upsert — ONE DB call for all videos ──────────────────────
        # The UNIQUE constraint on videos.video_id means upsert will UPDATE
        # existing rows and INSERT new ones atomically.
        try:
            supabase.table("videos").upsert(
                video_rows,
                on_conflict="video_id",
            ).execute()
            videos_synced = len(video_rows)
            logger.info(f"Batch upserted {videos_synced} videos in 1 DB call")
        except Exception as exc:
            logger.error(f"Batch upsert failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save videos to database: {exc}",
            )

        # ── 7. Update channel last_synced_at ──────────────────────────────────
        supabase.table("youtube_channels").update({
            "last_synced_at": datetime.utcnow().isoformat(),
        }).eq("id", channel_db_id).execute()

        return ChannelSyncResponse(
            channel=YouTubeService._channel_row_to_response(channel_data),
            videos_synced=videos_synced,
            message=f"Successfully synced {videos_synced} videos",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # VIDEO QUERIES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_channel_videos(
        channel_db_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[VideoResponse]:
        """
        Return videos from the database (not from YouTube API).
        Ordered by published_at descending.
        """
        supabase = get_supabase()
        try:
            resp = (
                supabase.table("videos")
                .select("*")
                .eq("channel_id", channel_db_id)
                .eq("user_id", user_id)
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )

            videos = []
            for row in resp.data:
                videos.append(VideoResponse(
                    id=row["id"],
                    user_id=row["user_id"],
                    channel_id=row["channel_id"],
                    video_id=row["video_id"],
                    title=row["title"],
                    description=row.get("description"),
                    thumbnail_url=row.get("thumbnail_url"),
                    duration=row.get("duration"),
                    view_count=row.get("view_count", 0),
                    like_count=row.get("like_count", 0),
                    comment_count=row.get("comment_count", 0),
                    published_at=YouTubeService._parse_dt(row.get("published_at")),
                    tags=row.get("tags") or [],
                    category_id=row.get("category_id"),
                    seo_score=row.get("seo_score"),
                    last_analyzed_at=YouTubeService._parse_dt(row.get("last_analyzed_at")),
                    created_at=YouTubeService._parse_dt(row.get("created_at")) or datetime.utcnow(),
                    updated_at=YouTubeService._parse_dt(row.get("updated_at")),
                ))
            return videos

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get videos: {exc}",
            )
