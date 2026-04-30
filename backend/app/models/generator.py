"""
AI Content Generator Models
Pydantic models for content generation requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ==================== Request Models ====================

class AnalysisRequest(BaseModel):
    """Request model for niche analysis"""
    niche: str = Field(..., description="Content niche to analyze (e.g., 'machine learning tutorials')")
    region: str = Field("US", description="Region code (US, GB, IN, etc.)")
    category_id: Optional[str] = Field(None, description="YouTube category ID (optional)")
    limit: int = Field(50, ge=10, le=50, description="Number of videos to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "niche": "machine learning tutorials",
                "region": "US",
                "category_id": "28",
                "limit": 50
            }
        }


class GenerationRequest(BaseModel):
    """Base request model for content generation"""
    topic: str = Field(..., description="Video topic/subject")
    keywords: Optional[List[str]] = Field(None, description="Target keywords for SEO")
    tone: str = Field("professional", description="Content tone: professional, casual, enthusiastic, educational")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    video_length: Optional[str] = Field(None, description="Video length: short, medium, long")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "keywords": ["machine learning", "python", "tutorial"],
                "tone": "educational",
                "target_audience": "beginners",
                "video_length": "medium"
            }
        }


class TitleGenerationRequest(GenerationRequest):
    """Request model for title generation"""
    count: int = Field(5, ge=1, le=10, description="Number of titles to generate")


class DescriptionGenerationRequest(GenerationRequest):
    """Request model for description generation"""
    title: Optional[str] = Field(None, description="Video title for context")
    include_timestamps: bool = Field(True, description="Include timestamp placeholders")
    include_links: bool = Field(True, description="Include link placeholders")
    include_cta: bool = Field(True, description="Include call-to-action")


class TagsGenerationRequest(GenerationRequest):
    """Request model for tags generation"""
    title: Optional[str] = Field(None, description="Video title for context")
    count: int = Field(15, ge=5, le=30, description="Number of tags to generate")


class ThumbnailTextRequest(GenerationRequest):
    """Request model for thumbnail text suggestions"""
    title: Optional[str] = Field(None, description="Video title for context")
    count: int = Field(5, ge=1, le=10, description="Number of suggestions")


class BatchGenerationRequest(BaseModel):
    """Request model for batch generation of all content types"""
    topic: str = Field(..., description="Video topic/subject")
    keywords: Optional[List[str]] = Field(None, description="Target keywords")
    tone: str = Field("professional", description="Content tone")
    target_audience: Optional[str] = Field(None, description="Target audience")
    video_length: Optional[str] = Field(None, description="Video length")
    title_count: int = Field(5, ge=1, le=10, description="Number of titles")
    tag_count: int = Field(15, ge=5, le=30, description="Number of tags")
    include_timestamps: bool = Field(True, description="Include timestamps in description")
    include_links: bool = Field(True, description="Include links in description")
    include_cta: bool = Field(True, description="Include CTA in description")
    thumbnail_count: int = Field(5, ge=1, le=10, description="Number of thumbnail suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "keywords": ["machine learning", "python", "tutorial"],
                "tone": "educational",
                "target_audience": "beginners",
                "video_length": "medium",
                "title_count": 5,
                "tag_count": 15,
                "include_timestamps": True,
                "include_links": True,
                "include_cta": True,
                "thumbnail_count": 5
            }
        }


# ==================== Response Models ====================

class ContentPattern(BaseModel):
    """Pattern extracted from trending videos"""
    keyword: str = Field(..., description="Keyword or pattern")
    frequency: int = Field(..., description="How many times it appears")
    avg_viral_score: float = Field(..., description="Average viral score of videos with this keyword")
    avg_engagement_rate: float = Field(..., description="Average engagement rate")


class AnalysisResponse(BaseModel):
    """Response model for niche analysis"""
    top_keywords: List[ContentPattern] = Field(..., description="Top keywords from trending videos")
    common_title_patterns: List[str] = Field(..., description="Common title structures")
    avg_viral_score: float = Field(..., description="Average viral score of analyzed videos")
    avg_engagement_rate: float = Field(..., description="Average engagement rate")
    total_videos_analyzed: int = Field(..., description="Number of videos analyzed")
    opportunities: List[str] = Field(..., description="Identified content opportunities")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class GeneratedContent(BaseModel):
    """Model for saved generated content"""
    id: str = Field(..., description="Unique content ID")
    user_id: str = Field(..., description="User ID")
    content_type: str = Field(..., description="Type: title, tags, description, thumbnail_text")
    content: Dict = Field(..., description="Generated content data")
    quality_score: float = Field(..., ge=0, le=100, description="Quality score")
    generated_at: datetime = Field(..., description="Generation timestamp")
    video_id: Optional[str] = Field(None, description="Associated video ID")
    batch_id: Optional[str] = Field(None, description="Associated batch ID")
    
    class Config:
        from_attributes = True


class BatchGenerationResponse(BaseModel):
    """Response model for batch generation"""
    batch_id: str = Field(..., description="Unique batch ID")
    titles: List[Dict] = Field(..., description="Generated titles")
    tags: Dict = Field(..., description="Generated tags")
    description: Dict = Field(..., description="Generated description")
    thumbnail_text: List[Dict] = Field(..., description="Generated thumbnail text")
    generated_at: datetime = Field(..., description="Generation timestamp")
    quality_scores: Dict[str, float] = Field(..., description="Quality scores by content type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_123456",
                "titles": [{"text": "...", "score": 87, "reasoning": "..."}],
                "tags": {"tags": [...], "tag_count": 15, "tag_categories": {...}},
                "description": {"description": "...", "word_count": 245, ...},
                "thumbnail_text": [{"text": "...", "style": "bold", "reasoning": "..."}],
                "generated_at": "2024-01-15T10:35:00Z",
                "quality_scores": {"titles": 85.2, "tags": 82.1, "description": 88.5, "thumbnail_text": 79.8}
            }
        }


class GenerationStats(BaseModel):
    """User's generation statistics"""
    total_generations: int = Field(..., description="Total number of generations")
    by_type: Dict[str, int] = Field(..., description="Count by content type")
    avg_quality_score: float = Field(..., description="Average quality score")
    most_used_keywords: List[str] = Field(..., description="Most frequently used keywords")
    most_used_tones: List[str] = Field(..., description="Most frequently used tones")
    generation_trends: Dict[str, int] = Field(..., description="Generations by date")
    last_generation: Optional[datetime] = Field(None, description="Last generation timestamp")


class ContentHistoryResponse(BaseModel):
    """Response model for content history"""
    total_count: int = Field(..., description="Total items in history")
    items: List[GeneratedContent] = Field(..., description="History items")
    has_more: bool = Field(..., description="Whether there are more items")


class RegenerationRequest(BaseModel):
    """Request model for regenerating content"""
    content_id: str = Field(..., description="ID of content to regenerate")
    count: Optional[int] = Field(None, description="Number of variations (for titles/tags/thumbnails)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "content_123",
                "count": 5
            }
        }


class ContentFeedbackRequest(BaseModel):
    """Request model for providing feedback on generated content"""
    content_id: str = Field(..., description="ID of content")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = Field(None, description="Optional feedback text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "content_123",
                "rating": 4,
                "feedback": "Great title, very catchy!"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error_id: str = Field(..., description="Unique error ID for support")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

