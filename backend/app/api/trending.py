"""
Trending Topics API Routes
Endpoints for trending video analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional, List
from app.models.user import UserResponse
from app.models.trending import (
    TrendingFetchRequest, TrendingFilterRequest,
    TrendingVideoResponse, TrendingAnalysis,
    TrendingDashboardResponse, TrendingStatsResponse,
    ContentOpportunity, YouTubeCategory, YOUTUBE_CATEGORIES
)
from app.services.trending_service import trending_service
from app.api.auth import get_current_user
from datetime import datetime


router = APIRouter(prefix="/trending", tags=["Trending Topics"])


@router.post("/fetch", response_model=List[TrendingVideoResponse])
async def fetch_trending_videos(
    request: TrendingFetchRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Fetch trending videos from YouTube API
    
    - **region**: Region code (US, GB, IN, etc.) (default: US)
    - **category_id**: YouTube category ID (optional)
    - **max_results**: Maximum results (1-50) (default: 50)
    
    This endpoint fetches the latest trending videos from YouTube and stores them in the database.
    The fetch happens in the background, so the response is immediate.
    
    **Note**: Requires YouTube API key to be configured.
    """
    try:
        # Fetch trending videos
        videos = await trending_service.fetch_trending_videos(
            region=request.region,
            category_id=request.category_id,
            max_results=request.max_results
        )
        
        return videos
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending videos: {str(e)}"
        )


@router.post("/filter", response_model=List[TrendingVideoResponse])
async def filter_trending_videos(
    request: TrendingFilterRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get trending videos with filters
    
    - **keywords**: Filter by keywords in title/description (optional)
    - **min_views**: Minimum view count (optional)
    - **min_viral_score**: Minimum viral score (0-100) (optional)
    - **category_id**: Filter by category (optional)
    - **region**: Region code (default: US)
    - **limit**: Maximum results (1-50) (default: 20)
    
    Returns trending videos from the database that match the specified filters.
    """
    try:
        videos = await trending_service.get_trending_videos(
            keywords=request.keywords,
            min_views=request.min_views,
            min_viral_score=request.min_viral_score,
            category_id=request.category_id,
            region=request.region,
            limit=request.limit
        )
        
        return videos
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter trending videos: {str(e)}"
        )


@router.get("/videos/{video_id}/analyze", response_model=TrendingAnalysis)
async def analyze_trending_video(
    video_id: str,
    niche: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze a specific trending video in detail
    
    - **video_id**: Trending video database ID (required)
    - **niche**: User's content niche for match scoring (optional)
    
    Returns detailed analysis including:
    - Viral score breakdown
    - Niche match score (if niche provided)
    - Opportunity score
    - Key insights
    """
    try:
        analysis = await trending_service.analyze_trending_video(
            video_id=video_id,
            user_niche=niche
        )
        
        return analysis
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trending video not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trending video: {str(e)}"
        )


@router.get("/stats", response_model=TrendingStatsResponse)
async def get_trending_stats(
    region: str = "US",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get statistics about trending videos
    
    - **region**: Region code (default: US)
    
    Returns:
    - Total trending videos
    - Average views
    - Average viral score
    - Top categories
    - Trending keywords
    - Last fetch time
    """
    try:
        stats = await trending_service.get_trending_stats(region=region)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending stats: {str(e)}"
        )


@router.get("/dashboard", response_model=TrendingDashboardResponse)
async def get_trending_dashboard(
    region: str = "US",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get trending dashboard data
    
    - **region**: Region code (default: US)
    
    Returns dashboard data including:
    - Total trending videos
    - Videos by category
    - Top viral videos
    - Average viral score
    - Last update time
    """
    try:
        # Get all trending videos
        all_videos = await trending_service.get_trending_videos(
            region=region,
            limit=50
        )
        
        # Get top viral videos
        top_viral = sorted(all_videos, key=lambda x: x.viral_score, reverse=True)[:10]
        
        # Group by category
        by_category = {}
        for video in all_videos:
            category_name = YOUTUBE_CATEGORIES.get(video.category_id, "Unknown")
            if category_name not in by_category:
                by_category[category_name] = 0
            by_category[category_name] += 1
        
        # Calculate average viral score
        avg_viral_score = sum(v.viral_score for v in all_videos) / len(all_videos) if all_videos else 0
        
        # Get last update time
        last_updated = max(v.fetched_at for v in all_videos) if all_videos else datetime.utcnow()
        
        return TrendingDashboardResponse(
            total_trending=len(all_videos),
            by_category=by_category,
            top_viral_videos=top_viral,
            average_viral_score=round(avg_viral_score, 2),
            last_updated=last_updated
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending dashboard: {str(e)}"
        )


@router.get("/opportunities", response_model=List[ContentOpportunity])
async def get_content_opportunities(
    niche: str,
    region: str = "US",
    limit: int = 5,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Identify content opportunities based on trending videos
    
    - **niche**: User's content niche (required)
    - **region**: Region code (default: US)
    - **limit**: Maximum opportunities (default: 5)
    
    Returns content opportunities that match the user's niche, including:
    - Topic/keyword clusters
    - Competition level
    - Opportunity score
    - Recommended approach
    - Sample titles
    """
    try:
        opportunities = await trending_service.identify_content_opportunities(
            user_niche=niche,
            region=region,
            limit=limit
        )
        
        return opportunities
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify content opportunities: {str(e)}"
        )


@router.get("/categories", response_model=List[YouTubeCategory])
async def get_youtube_categories(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of YouTube video categories
    
    Returns all available YouTube categories with their IDs and names.
    Use these category IDs when fetching or filtering trending videos.
    """
    categories = [
        YouTubeCategory(id=cat_id, name=name)
        for cat_id, name in YOUTUBE_CATEGORIES.items()
    ]
    
    return sorted(categories, key=lambda x: x.name)


@router.get("/regions")
async def get_supported_regions(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of supported region codes
    
    Returns common region codes that can be used for fetching trending videos.
    """
    regions = [
        {"code": "US", "name": "United States"},
        {"code": "GB", "name": "United Kingdom"},
        {"code": "CA", "name": "Canada"},
        {"code": "AU", "name": "Australia"},
        {"code": "IN", "name": "India"},
        {"code": "DE", "name": "Germany"},
        {"code": "FR", "name": "France"},
        {"code": "JP", "name": "Japan"},
        {"code": "KR", "name": "South Korea"},
        {"code": "BR", "name": "Brazil"},
        {"code": "MX", "name": "Mexico"},
        {"code": "ES", "name": "Spain"},
        {"code": "IT", "name": "Italy"},
        {"code": "RU", "name": "Russia"},
        {"code": "NL", "name": "Netherlands"},
    ]
    
    return regions
