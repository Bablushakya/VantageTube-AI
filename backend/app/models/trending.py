"""
Trending Topics Models
Pydantic models for trending video analysis
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TrendingVideoBase(BaseModel):
    """Base model for trending video"""
    youtube_video_id: str
    title: str
    channel_title: str
    channel_id: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    category_id: str
    tags: List[str] = []


class TrendingVideoCreate(TrendingVideoBase):
    """Model for creating trending video"""
    viral_score: float
    engagement_rate: float
    trending_rank: int
    region: str = "US"


class TrendingVideoResponse(TrendingVideoBase):
    """Response model for trending video"""
    id: str
    viral_score: float
    engagement_rate: float
    trending_rank: int
    region: str
    fetched_at: datetime
    
    class Config:
        from_attributes = True


class TrendingFetchRequest(BaseModel):
    """Request model for fetching trending videos"""
    region: str = Field("US", description="Region code (US, GB, IN, etc.)")
    category_id: Optional[str] = Field(None, description="YouTube category ID (optional)")
    max_results: int = Field(50, ge=1, le=50, description="Maximum results (1-50)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "region": "US",
                "category_id": "28",
                "max_results": 50
            }
        }


class TrendingFilterRequest(BaseModel):
    """Request model for filtering trending videos"""
    keywords: Optional[List[str]] = Field(None, description="Filter by keywords in title/description")
    min_views: Optional[int] = Field(None, description="Minimum view count")
    min_viral_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum viral score")
    category_id: Optional[str] = Field(None, description="Filter by category")
    region: str = Field("US", description="Region code")
    limit: int = Field(20, ge=1, le=50, description="Maximum results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "keywords": ["tutorial", "guide"],
                "min_views": 10000,
                "min_viral_score": 70,
                "category_id": "28",
                "region": "US",
                "limit": 20
            }
        }


class ViralScoreBreakdown(BaseModel):
    """Breakdown of viral score calculation"""
    view_velocity: float = Field(..., description="Views per hour since publish")
    engagement_rate: float = Field(..., description="(likes + comments) / views")
    like_ratio: float = Field(..., description="likes / views")
    comment_ratio: float = Field(..., description="comments / views")
    recency_bonus: float = Field(..., description="Bonus for recent videos")
    total_score: float = Field(..., ge=0, le=100, description="Overall viral score")


class TrendingAnalysis(BaseModel):
    """Analysis of trending video"""
    video: TrendingVideoResponse
    viral_score_breakdown: ViralScoreBreakdown
    niche_match: Optional[float] = Field(None, description="Match score with user's niche (0-100)")
    opportunity_score: Optional[float] = Field(None, description="Content opportunity score (0-100)")
    insights: List[str] = Field(default_factory=list, description="Key insights about the trend")


class TrendingDashboardResponse(BaseModel):
    """Response model for trending dashboard"""
    total_trending: int
    by_category: dict
    top_viral_videos: List[TrendingVideoResponse]
    average_viral_score: float
    last_updated: datetime


class TrendingStatsResponse(BaseModel):
    """Statistics about trending videos"""
    total_videos: int
    average_views: int
    average_viral_score: float
    top_categories: List[dict]
    trending_keywords: List[dict]
    last_fetch: Optional[datetime]


class YouTubeCategory(BaseModel):
    """YouTube video category"""
    id: str
    name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "28",
                "name": "Science & Technology"
            }
        }


# YouTube Category Mapping
YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism"
}


class NicheRecommendation(BaseModel):
    """Niche recommendation based on trending analysis"""
    niche: str
    trending_count: int
    average_viral_score: float
    opportunity_score: float
    sample_videos: List[TrendingVideoResponse]
    insights: List[str]


class ContentOpportunity(BaseModel):
    """Content opportunity identified from trends"""
    topic: str
    keyword_cluster: List[str]
    trending_videos_count: int
    average_views: int
    competition_level: str = Field(..., description="Low, Medium, High")
    opportunity_score: float = Field(..., ge=0, le=100)
    recommended_approach: str
    sample_titles: List[str]
