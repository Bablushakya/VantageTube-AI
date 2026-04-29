"""
VantageTube AI - SEO Models
Pydantic models for SEO analysis data validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SEOCriterion(BaseModel):
    """Individual SEO criterion"""
    name: str
    score: int  # 0-100
    weight: float  # Weight in overall score
    status: str  # 'excellent', 'good', 'fair', 'poor'
    message: str
    details: Optional[str] = None


class SEOSuggestion(BaseModel):
    """SEO improvement suggestion"""
    type: str  # 'title', 'description', 'tags', 'thumbnail', 'engagement'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    impact: str  # Expected impact description


class SEOReportBase(BaseModel):
    """Base SEO report model"""
    overall_score: int  # 0-100
    title_score: Optional[int] = None
    description_score: Optional[int] = None
    tags_score: Optional[int] = None
    thumbnail_score: Optional[int] = None
    engagement_score: Optional[int] = None


class SEOReportCreate(SEOReportBase):
    """Model for creating SEO report"""
    user_id: str
    video_id: str
    suggestions: List[Dict[str, Any]]
    criteria_breakdown: Dict[str, Any]


class SEOReportResponse(SEOReportBase):
    """Model for SEO report response"""
    id: str
    user_id: str
    video_id: str
    suggestions: List[SEOSuggestion]
    criteria_breakdown: List[SEOCriterion]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis"""
    video_id: str  # Database video ID
    force_reanalysis: Optional[bool] = False


class VideoAnalysisResponse(BaseModel):
    """Response model for video analysis"""
    video_id: str
    video_title: str
    overall_score: int
    grade: str  # 'Excellent', 'Good', 'Average', 'Poor', 'Critical'
    criteria: List[SEOCriterion]
    suggestions: List[SEOSuggestion]
    analyzed_at: datetime
