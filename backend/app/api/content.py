"""
Content Generation API Routes
Endpoints for AI-powered content generation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.models.user import UserResponse
from app.models.content import (
    TitleGenerationRequest, DescriptionGenerationRequest,
    TagsGenerationRequest, ThumbnailTextRequest,
    GeneratedTitles, GeneratedDescription, GeneratedTags,
    GeneratedThumbnailText, SaveGeneratedContentRequest,
    GeneratedContentResponse, ContentHistoryResponse
)
from app.services.ai_service import ai_service
from app.services.content_service import content_service
from app.api.auth import get_current_user


router = APIRouter(prefix="/content", tags=["Content Generation"])


@router.post("/generate/titles", response_model=GeneratedTitles)
async def generate_titles(
    request: TitleGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video titles
    
    - **topic**: Video topic/subject (required)
    - **keywords**: Target keywords for SEO (optional)
    - **tone**: Content tone (professional, casual, enthusiastic, educational)
    - **target_audience**: Target audience description (optional)
    - **count**: Number of titles to generate (1-10, default: 5)
    
    Returns multiple optimized title options with SEO scores and reasoning.
    """
    try:
        # Validate inputs
        if not request.topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic is required"
            )
        
        # Generate titles using AI
        titles = await ai_service.generate_titles(
            topic=request.topic,
            keywords=request.keywords or [],
            tone=request.tone,
            target_audience=request.target_audience,
            count=request.count
        )
        
        # Save to history
        await content_service.save_generated_content(
            user_id=current_user.id,
            content_type="title",
            content=titles.dict(),
            video_id=request.video_id,
            prompt_used=f"Topic: {request.topic}, Keywords: {request.keywords}"
        )
        
        return titles
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate titles: {str(e)}"
        )


@router.post("/generate/description", response_model=GeneratedDescription)
async def generate_description(
    request: DescriptionGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video description
    
    - **topic**: Video topic/subject (required)
    - **title**: Video title for context (optional)
    - **keywords**: Target keywords for SEO (optional)
    - **tone**: Content tone (professional, casual, enthusiastic, educational)
    - **target_audience**: Target audience description (optional)
    - **video_length**: Video length (short, medium, long) (optional)
    - **include_timestamps**: Include timestamp placeholders (default: true)
    - **include_links**: Include link placeholders (default: true)
    - **include_cta**: Include call-to-action (default: true)
    
    Returns optimized description with SEO tips.
    """
    try:
        # Validate inputs
        if not request.topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic is required"
            )
        
        # Generate description using AI
        description = await ai_service.generate_description(
            topic=request.topic,
            title=request.title,
            keywords=request.keywords or [],
            tone=request.tone,
            target_audience=request.target_audience,
            video_length=request.video_length,
            include_timestamps=request.include_timestamps,
            include_links=request.include_links,
            include_cta=request.include_cta
        )
        
        # Save to history
        await content_service.save_generated_content(
            user_id=current_user.id,
            content_type="description",
            content=description.dict(),
            video_id=request.video_id,
            prompt_used=f"Topic: {request.topic}, Title: {request.title}"
        )
        
        return description
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate description: {str(e)}"
        )


@router.post("/generate/tags", response_model=GeneratedTags)
async def generate_tags(
    request: TagsGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video tags
    
    - **topic**: Video topic/subject (required)
    - **title**: Video title for context (optional)
    - **keywords**: Target keywords (optional)
    - **count**: Number of tags to generate (5-30, default: 15)
    
    Returns categorized tags (primary, secondary, long-tail, broad).
    """
    try:
        # Validate inputs
        if not request.topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic is required"
            )
        
        # Generate tags using AI
        tags = await ai_service.generate_tags(
            topic=request.topic,
            title=request.title,
            keywords=request.keywords or [],
            count=request.count
        )
        
        # Save to history
        await content_service.save_generated_content(
            user_id=current_user.id,
            content_type="tags",
            content=tags.dict(),
            video_id=request.video_id,
            prompt_used=f"Topic: {request.topic}, Title: {request.title}"
        )
        
        return tags
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tags: {str(e)}"
        )


@router.post("/generate/thumbnail-text", response_model=GeneratedThumbnailText)
async def generate_thumbnail_text(
    request: ThumbnailTextRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered thumbnail text suggestions
    
    - **topic**: Video topic/subject (required)
    - **title**: Video title for context (optional)
    - **count**: Number of suggestions (1-10, default: 5)
    
    Returns thumbnail text suggestions with styles and design tips.
    """
    try:
        # Validate inputs
        if not request.topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic is required"
            )
        
        # Generate thumbnail text using AI
        thumbnail_text = await ai_service.generate_thumbnail_text(
            topic=request.topic,
            title=request.title,
            count=request.count
        )
        
        # Save to history
        await content_service.save_generated_content(
            user_id=current_user.id,
            content_type="thumbnail_text",
            content=thumbnail_text.dict(),
            video_id=request.video_id,
            prompt_used=f"Topic: {request.topic}, Title: {request.title}"
        )
        
        return thumbnail_text
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate thumbnail text: {str(e)}"
        )


@router.get("/history", response_model=ContentHistoryResponse)
async def get_content_history(
    content_type: Optional[str] = None,
    video_id: Optional[str] = None,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's content generation history
    
    - **content_type**: Filter by type (title, description, tags, thumbnail_text) (optional)
    - **video_id**: Filter by video ID (optional)
    - **limit**: Maximum number of results (default: 50)
    
    Returns list of previously generated content.
    """
    try:
        history = await content_service.get_user_content_history(
            user_id=current_user.id,
            content_type=content_type,
            video_id=video_id,
            limit=limit
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content history: {str(e)}"
        )


@router.get("/history/{content_id}", response_model=GeneratedContentResponse)
async def get_content_by_id(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific generated content by ID
    
    Returns the generated content details.
    """
    try:
        content = await content_service.get_content_by_id(
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content: {str(e)}"
        )


@router.delete("/history/{content_id}")
async def delete_content(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete generated content from history
    
    Returns success message.
    """
    try:
        deleted = await content_service.delete_content(
            content_id=content_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return {"message": "Content deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content: {str(e)}"
        )


@router.get("/stats")
async def get_content_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's content generation statistics
    
    Returns statistics about generated content (total, by type, recent).
    """
    try:
        stats = await content_service.get_content_stats(
            user_id=current_user.id
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content stats: {str(e)}"
        )
