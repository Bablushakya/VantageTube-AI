"""
VantageTube AI - SEO Analysis API Routes
Handles video SEO analysis endpoints
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from app.models.seo import VideoAnalysisRequest, VideoAnalysisResponse
from app.services.seo_service import SEOService
from app.api.auth import get_current_user_id


router = APIRouter(prefix="/seo", tags=["SEO Analysis"])


@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(
    request: VideoAnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Analyze video SEO
    
    Performs comprehensive SEO analysis on a video including:
    - Title optimization (length, keywords, power words)
    - Description optimization (length, links, timestamps, CTAs)
    - Tags optimization (count, relevance, variety)
    - Thumbnail optimization (presence, best practices)
    - Engagement metrics (like ratio, comment ratio, engagement rate)
    
    Returns overall score (0-100), grade, detailed criteria breakdown, and improvement suggestions.
    
    - **video_id**: Video database ID (not YouTube video ID)
    - **force_reanalysis**: Force new analysis even if recent one exists (default: false)
    
    Note: Analysis is cached for 24 hours unless force_reanalysis is true
    """
    return await SEOService.analyze_video(
        request.video_id,
        user_id,
        request.force_reanalysis
    )


@router.get("/videos/{video_id}/reports")
async def get_video_reports(
    video_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all SEO reports for a video
    
    Returns historical SEO analysis reports for a video, ordered by date (newest first).
    Useful for tracking SEO improvements over time.
    
    - **video_id**: Video database ID
    
    Returns list of SEO reports with scores, criteria, and suggestions
    """
    return await SEOService.get_video_reports(video_id, user_id)


@router.get("/dashboard/stats")
async def get_seo_dashboard_stats(user_id: str = Depends(get_current_user_id)):
    """
    Get SEO dashboard statistics
    
    Returns aggregate SEO statistics for all user's videos:
    - Average SEO score
    - Total videos analyzed
    - Score distribution
    - Recent analyses
    
    Useful for dashboard overview
    """
    from app.core.supabase import get_supabase
    supabase = get_supabase()
    
    # Get all videos with SEO scores
    videos_response = supabase.table("videos").select("seo_score, last_analyzed_at").eq("user_id", user_id).execute()
    
    videos = videos_response.data
    analyzed_videos = [v for v in videos if v.get("seo_score") is not None]
    
    if not analyzed_videos:
        return {
            "total_videos": len(videos),
            "analyzed_videos": 0,
            "average_score": 0,
            "score_distribution": {
                "excellent": 0,  # 90-100
                "good": 0,       # 75-89
                "average": 0,    # 60-74
                "poor": 0,       # 40-59
                "critical": 0    # 0-39
            },
            "recent_analyses": []
        }
    
    # Calculate statistics
    total_score = sum(v["seo_score"] for v in analyzed_videos)
    average_score = int(total_score / len(analyzed_videos))
    
    # Score distribution
    distribution = {
        "excellent": len([v for v in analyzed_videos if v["seo_score"] >= 90]),
        "good": len([v for v in analyzed_videos if 75 <= v["seo_score"] < 90]),
        "average": len([v for v in analyzed_videos if 60 <= v["seo_score"] < 75]),
        "poor": len([v for v in analyzed_videos if 40 <= v["seo_score"] < 60]),
        "critical": len([v for v in analyzed_videos if v["seo_score"] < 40])
    }
    
    # Recent analyses
    recent = sorted(
        [v for v in analyzed_videos if v.get("last_analyzed_at")],
        key=lambda x: x["last_analyzed_at"],
        reverse=True
    )[:5]
    
    return {
        "total_videos": len(videos),
        "analyzed_videos": len(analyzed_videos),
        "average_score": average_score,
        "score_distribution": distribution,
        "recent_analyses": recent
    }
