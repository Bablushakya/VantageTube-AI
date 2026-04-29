"""
Content Generation Models
Pydantic models for AI-generated content
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    video_id: Optional[str] = Field(None, description="Video ID for context (optional)")
    topic: Optional[str] = Field(None, description="Video topic/subject")
    keywords: Optional[List[str]] = Field(None, description="Target keywords")
    tone: Optional[str] = Field("professional", description="Content tone: professional, casual, enthusiastic, educational")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    video_length: Optional[str] = Field(None, description="Video length: short (<5min), medium (5-15min), long (>15min)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "How to build a REST API with FastAPI",
                "keywords": ["fastapi", "python", "rest api", "tutorial"],
                "tone": "educational",
                "target_audience": "beginner developers",
                "video_length": "medium"
            }
        }


class TitleGenerationRequest(ContentGenerationRequest):
    """Request model for title generation"""
    count: int = Field(5, ge=1, le=10, description="Number of titles to generate")


class DescriptionGenerationRequest(ContentGenerationRequest):
    """Request model for description generation"""
    title: Optional[str] = Field(None, description="Video title for context")
    include_timestamps: bool = Field(True, description="Include timestamp placeholders")
    include_links: bool = Field(True, description="Include link placeholders")
    include_cta: bool = Field(True, description="Include call-to-action")


class TagsGenerationRequest(ContentGenerationRequest):
    """Request model for tags generation"""
    title: Optional[str] = Field(None, description="Video title for context")
    count: int = Field(15, ge=5, le=30, description="Number of tags to generate")


class ThumbnailTextRequest(ContentGenerationRequest):
    """Request model for thumbnail text suggestions"""
    title: Optional[str] = Field(None, description="Video title for context")
    count: int = Field(5, ge=1, le=10, description="Number of suggestions")


class GeneratedTitle(BaseModel):
    """Single generated title"""
    text: str
    score: int = Field(..., ge=0, le=100, description="SEO score estimate")
    reasoning: str = Field(..., description="Why this title works")


class GeneratedTitles(BaseModel):
    """Response model for title generation"""
    titles: List[GeneratedTitle]
    topic: str
    keywords: List[str]
    generated_at: datetime


class GeneratedDescription(BaseModel):
    """Response model for description generation"""
    description: str
    word_count: int
    includes_timestamps: bool
    includes_links: bool
    includes_cta: bool
    seo_tips: List[str]
    generated_at: datetime


class GeneratedTags(BaseModel):
    """Response model for tags generation"""
    tags: List[str]
    tag_count: int
    tag_categories: dict = Field(..., description="Tags grouped by category")
    generated_at: datetime


class ThumbnailTextSuggestion(BaseModel):
    """Single thumbnail text suggestion"""
    text: str
    style: str = Field(..., description="Suggested style: bold, minimal, question, number")
    reasoning: str


class GeneratedThumbnailText(BaseModel):
    """Response model for thumbnail text suggestions"""
    suggestions: List[ThumbnailTextSuggestion]
    design_tips: List[str]
    generated_at: datetime


class SaveGeneratedContentRequest(BaseModel):
    """Request to save generated content"""
    video_id: Optional[str] = Field(None, description="Associated video ID")
    content_type: str = Field(..., description="Type: title, description, tags, thumbnail_text")
    content: dict = Field(..., description="Generated content data")
    prompt_used: Optional[str] = Field(None, description="Prompt used for generation")


class GeneratedContentResponse(BaseModel):
    """Response model for saved generated content"""
    id: str
    user_id: str
    video_id: Optional[str]
    content_type: str
    content: dict
    prompt_used: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentHistoryResponse(BaseModel):
    """Response model for content generation history"""
    total_count: int
    items: List[GeneratedContentResponse]
