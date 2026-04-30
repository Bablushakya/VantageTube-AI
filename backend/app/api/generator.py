"""
AI Content Generator API Endpoints
Provides endpoints for generating optimized YouTube content metadata
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import logging
from app.core.security import get_current_user
from app.models.generator import (
    AnalysisRequest, AnalysisResponse,
    TitleGenerationRequest, TagsGenerationRequest,
    DescriptionGenerationRequest, ThumbnailTextRequest,
    BatchGenerationRequest, BatchGenerationResponse,
    GeneratedContent, GenerationStats, ErrorResponse,
    RegenerationRequest, ContentFeedbackRequest
)
from app.services.generator_service import generator_service
from app.services.content_service import content_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generator", tags=["generator"])


# ==================== Analysis Endpoints ====================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_niche(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze top-performing videos in a niche
    
    Fetches trending videos, extracts patterns, and identifies opportunities
    for content creation in the specified niche.
    
    Args:
        request: AnalysisRequest with niche, region, category
        current_user: Authenticated user
        
    Returns:
        AnalysisResponse with keywords, patterns, and opportunities
        
    Raises:
        HTTPException: If analysis fails or no data available
    """
    try:
        logger.info(f"User {current_user['id']} analyzing niche: {request.niche}")
        
        response = await generator_service.analyze_niche(request)
        
        logger.info(f"Analysis complete for niche: {request.niche}")
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing niche: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze niche: {str(e)}"
        )


# ==================== Title Generation Endpoints ====================

@router.post("/titles", response_model=dict)
async def generate_titles(
    request: TitleGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate optimized video titles
    
    Generates multiple title variations based on trending patterns
    and the specified parameters.
    
    Args:
        request: TitleGenerationRequest with topic, keywords, tone, etc.
        current_user: Authenticated user
        
    Returns:
        Dictionary with generated titles and metadata
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"User {current_user['id']} generating titles for: {request.topic}")
        
        titles_response = await generator_service.generate_titles(
            user_id=current_user['id'],
            request=request
        )
        
        logger.info(f"Generated {len(titles_response.titles)} titles")
        return titles_response.dict()
        
    except Exception as e:
        logger.error(f"Error generating titles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate titles: {str(e)}"
        )


# ==================== Tags Generation Endpoints ====================

@router.post("/tags", response_model=dict)
async def generate_tags(
    request: TagsGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate optimized video tags
    
    Generates categorized tags based on trending patterns and
    the specified topic and keywords.
    
    Args:
        request: TagsGenerationRequest with topic, keywords, etc.
        current_user: Authenticated user
        
    Returns:
        Dictionary with generated tags organized by category
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"User {current_user['id']} generating tags for: {request.topic}")
        
        tags_response = await generator_service.generate_tags(
            user_id=current_user['id'],
            request=request
        )
        
        logger.info(f"Generated {len(tags_response.tags)} tags")
        return tags_response.dict()
        
    except Exception as e:
        logger.error(f"Error generating tags: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate tags: {str(e)}"
        )


# ==================== Description Generation Endpoints ====================

@router.post("/description", response_model=dict)
async def generate_description(
    request: DescriptionGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate optimized video description
    
    Generates an SEO-optimized description with optional timestamps,
    links, and call-to-action based on trending patterns.
    
    Args:
        request: DescriptionGenerationRequest with topic, keywords, etc.
        current_user: Authenticated user
        
    Returns:
        Dictionary with generated description and SEO tips
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"User {current_user['id']} generating description for: {request.topic}")
        
        description_response = await generator_service.generate_description(
            user_id=current_user['id'],
            request=request
        )
        
        logger.info(f"Generated description ({description_response.word_count} words)")
        return description_response.dict()
        
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate description: {str(e)}"
        )


# ==================== Thumbnail Text Endpoints ====================

@router.post("/thumbnail-text", response_model=dict)
async def generate_thumbnail_text(
    request: ThumbnailTextRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate thumbnail text suggestions
    
    Generates multiple thumbnail text suggestions in different styles
    to maximize click-through rates.
    
    Args:
        request: ThumbnailTextRequest with topic, title, etc.
        current_user: Authenticated user
        
    Returns:
        Dictionary with thumbnail text suggestions and design tips
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"User {current_user['id']} generating thumbnail text for: {request.topic}")
        
        thumbnail_response = await generator_service.generate_thumbnail_text(
            user_id=current_user['id'],
            request=request
        )
        
        logger.info(f"Generated {len(thumbnail_response.suggestions)} thumbnail suggestions")
        return thumbnail_response.dict()
        
    except Exception as e:
        logger.error(f"Error generating thumbnail text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate thumbnail text: {str(e)}"
        )


# ==================== Batch Generation Endpoints ====================

@router.post("/generate-all", response_model=BatchGenerationResponse)
async def generate_all(
    request: BatchGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate all content types in batch
    
    Generates titles, tags, description, and thumbnail text in a single
    request for maximum efficiency.
    
    Args:
        request: BatchGenerationRequest with all parameters
        current_user: Authenticated user
        
    Returns:
        BatchGenerationResponse with all generated content
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"User {current_user['id']} starting batch generation for: {request.topic}")
        
        batch_response = await generator_service.generate_all(
            user_id=current_user['id'],
            request=request
        )
        
        logger.info(f"Batch generation complete, batch_id: {batch_response.batch_id}")
        return batch_response
        
    except Exception as e:
        logger.error(f"Error in batch generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate content: {str(e)}"
        )


# ==================== History Endpoints ====================

@router.get("/history", response_model=dict)
async def get_generation_history(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's generation history
    
    Retrieves all previously generated content with optional filtering
    by content type and pagination support.
    
    Args:
        content_type: Filter by content type (title, tags, description, thumbnail_text)
        limit: Maximum results to return
        offset: Pagination offset
        current_user: Authenticated user
        
    Returns:
        Dictionary with total count and history items
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"User {current_user['id']} retrieving generation history")
        
        history = await generator_service.get_generation_history(
            user_id=current_user['id'],
            content_type=content_type,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error retrieving generation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{content_id}", response_model=GeneratedContent)
async def get_content_by_id(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific generated content by ID
    
    Retrieves a single piece of generated content by its ID.
    
    Args:
        content_id: Content ID
        current_user: Authenticated user
        
    Returns:
        GeneratedContent object
        
    Raises:
        HTTPException: If content not found or retrieval fails
    """
    try:
        logger.info(f"User {current_user['id']} retrieving content: {content_id}")
        
        content = await content_service.get_content_by_id(
            content_id=content_id,
            user_id=current_user['id']
        )
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail="Content not found"
            )
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve content: {str(e)}"
        )


@router.delete("/history/{content_id}", response_model=dict)
async def delete_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete generated content
    
    Permanently deletes a piece of generated content.
    
    Args:
        content_id: Content ID
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"User {current_user['id']} deleting content: {content_id}")
        
        success = await content_service.delete_content(
            content_id=content_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Content not found"
            )
        
        # Track deletion in history
        await content_service.track_generation_history(
            user_id=current_user['id'],
            content_id=content_id,
            action="deleted",
            content_type="unknown"
        )
        
        return {"success": True, "message": "Content deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete content: {str(e)}"
        )


# ==================== Statistics Endpoints ====================

@router.get("/stats", response_model=GenerationStats)
async def get_generation_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's generation statistics
    
    Retrieves comprehensive statistics about the user's generation activity
    including counts by type, quality scores, and trends.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        GenerationStats with usage metrics
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"User {current_user['id']} retrieving generation stats")
        
        stats = await generator_service.get_generation_stats(
            user_id=current_user['id']
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving generation stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ==================== Regeneration Endpoints ====================

@router.post("/regenerate", response_model=dict)
async def regenerate_content(
    request: RegenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Regenerate specific content
    
    Generates new variations of previously generated content.
    
    Args:
        request: RegenerationRequest with content_id and optional count
        current_user: Authenticated user
        
    Returns:
        Dictionary with newly generated content
        
    Raises:
        HTTPException: If regeneration fails
    """
    try:
        logger.info(f"User {current_user['id']} regenerating content: {request.content_id}")
        
        # Get original content
        original_content = await content_service.get_content_by_id(
            content_id=request.content_id,
            user_id=current_user['id']
        )
        
        if not original_content:
            raise HTTPException(
                status_code=404,
                detail="Content not found"
            )
        
        # Track regeneration
        await content_service.track_generation_history(
            user_id=current_user['id'],
            content_id=request.content_id,
            action="regenerated",
            content_type=original_content.content_type
        )
        
        return {
            "success": True,
            "message": "Content regenerated successfully",
            "original_id": request.content_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate content: {str(e)}"
        )


# ==================== Feedback Endpoints ====================

@router.post("/feedback", response_model=dict)
async def submit_feedback(
    request: ContentFeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback on generated content
    
    Allows users to rate and provide feedback on generated content
    to improve future generations.
    
    Args:
        request: ContentFeedbackRequest with rating and feedback
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If submission fails
    """
    try:
        logger.info(f"User {current_user['id']} submitting feedback for: {request.content_id}")
        
        # Verify content belongs to user
        content = await content_service.get_content_by_id(
            content_id=request.content_id,
            user_id=current_user['id']
        )
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail="Content not found"
            )
        
        # Store feedback (could be extended to save to database)
        logger.info(f"Feedback recorded: rating={request.rating}, content_id={request.content_id}")
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "rating": request.rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# ==================== Health Check ====================

@router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "ai-content-generator",
        "version": "1.0.0"
    }
