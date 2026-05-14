"""
VantageTube AI - Video Analytics API Routes
Provides comprehensive analytics for selected videos.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional

from app.services.analytics_service import AnalyticsService
from app.api.auth import get_current_user_id


router = APIRouter(prefix="/videos", tags=["Analytics"])


@router.get("/{video_id}/analytics")
async def get_video_analytics(
    video_id: str,
    force_refresh: bool = Query(False, description="Ignore cache and fetch fresh data"),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get comprehensive analytics for a video.

    Returns performance metrics, traffic sources, audience insights,
    retention data, keyword performance, and rule-based insights.

    Data source priority:
    1. YouTube Analytics API (preferred)
    2. YouTube Data API
    3. Database cache (if available)
    4. Mock data fallback

    - **video_id**: Database video ID (not YouTube video ID)
    - **force_refresh**: If True, bypass cache and re-fetch from YouTube APIs

    Response includes:
    - video: Video metadata
    - metrics: Performance KPIs (views, watch time, CTR, etc.)
    - traffic_sources: Traffic source breakdown
    - audience: Demographic insights
    - retention: Audience retention data
    - keywords: Search keyword performance
    - insights: Rule-based content quality insights
    - performance_score: Overall 0-100 score
    - engagement_score: Engagement rate score
    - retention_score: Retention score
    - ctr_score: CTR score
    - classification: Viral/High Performer/Average/Underperforming
    """
    try:
        result = await AnalyticsService.get_video_analytics(video_id, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analytics data not available for this video",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}",
        )