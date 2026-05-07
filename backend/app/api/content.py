"""
Content Generation API Routes
Endpoints for AI-powered content generation with quota management and caching
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional
import logging
import math
import re
from datetime import datetime, timezone
from app.models.user import UserResponse
from app.models.content import (
    TitleGenerationRequest, DescriptionGenerationRequest,
    TagsGenerationRequest, ThumbnailTextRequest, ThumbnailGenerationRequest,
    GeneratedTitle, GeneratedTitles,
    GeneratedDescription, GeneratedTags,
    GeneratedThumbnailText, ThumbnailTextSuggestion,
    SaveGeneratedContentRequest,
    GeneratedContentResponse, ContentHistoryResponse
)
from app.services.ai_service import ai_service
from app.services.content_service import content_service
from app.services.nano_service import nano_service
from app.services.ai_quota_manager import quota_manager, QuotaStatus
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["Content Generation"])


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _check_quota_status(quota_status: QuotaStatus, quota_message: str, user_id: str):
    """
    Raise 429 with a Retry-After header if quota is not AVAILABLE.
    The global exception handler in main.py will add Retry-After to the
    response headers based on the detail message.
    """
    if quota_status != QuotaStatus.AVAILABLE:
        logger.warning(f"Quota exceeded for user {user_id}: {quota_message}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota exceeded: {quota_message}",
            # FastAPI passes headers kwarg through to the response
            headers={"Retry-After": _retry_after_from_message(quota_message)},
        )


def _is_gemini_quota_error(exc: Exception) -> bool:
    """
    Return True if the exception is a Google Gemini 429 / quota-exceeded error.
    Google raises these as generic Exception or google.api_core.exceptions.ResourceExhausted.
    We detect them by inspecting the string representation.
    """
    msg = str(exc).lower()
    return any(phrase in msg for phrase in (
        "quota exceeded",
        "you exceeded your current quota",
        "resource_exhausted",
        "generativelanguage.googleapis.com",
        "free_tier",
        "retry_delay",
    ))


def _gemini_retry_after(exc: Exception) -> int:
    """
    Extract the retry delay from a Gemini 429 error message.
    The message contains: 'Please retry in 50.775381752s.'
    Falls back to 60 if not found.
    """
    match = re.search(r'retry in (\d+(?:\.\d+)?)\s*s', str(exc), re.IGNORECASE)
    if match:
        return max(1, math.ceil(float(match.group(1))))
    # Also check retry_delay { seconds: N }
    match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', str(exc))
    if match:
        return max(1, int(match.group(1)))
    return 60


def _raise_gemini_quota_429(exc: Exception, user_id: str):
    """Convert a Gemini quota error into a proper HTTP 429 with Retry-After."""
    retry_after = _gemini_retry_after(exc)
    logger.warning(
        f"Gemini quota exceeded for user {user_id} — "
        f"Retry-After: {retry_after}s  detail: {str(exc)[:200]}"
    )
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            f"AI generation quota exceeded. "
            f"Please wait {retry_after} seconds before trying again. "
            f"(Gemini free tier limit reached)"
        ),
        headers={"Retry-After": str(retry_after)},
    )


def _retry_after_from_message(msg: str) -> str:
    """Return a Retry-After value (seconds as string) inferred from the quota message."""
    m = msg.lower()
    if "per day" in m or "daily" in m or "midnight" in m:
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return str(max(1, math.ceil((midnight - now).total_seconds())))
    if "per hour" in m:
        return "3600"
    if "per minute" in m or "rate limit" in m:
        return "60"
    return "60"


def _now() -> datetime:
    return datetime.utcnow()


# ─────────────────────────────────────────────────────────────────────────────
# QUOTA INFO
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/quota/info")
async def get_quota_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current quota usage for the authenticated user."""
    try:
        return {
            "user_id": current_user.id,
            "quota": quota_manager.get_quota_info(current_user.id),
            "message": "Quota information retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting quota info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quota information")


# ─────────────────────────────────────────────────────────────────────────────
# TITLE GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/titles", response_model=GeneratedTitles)
async def generate_titles(
    request: TitleGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video titles.
    Returns 429 when quota is exceeded.
    """
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        if not (1 <= request.count <= 10):
            raise HTTPException(status_code=400, detail="Count must be between 1 and 10")

        # Quota check
        qs, qm = await quota_manager.check_quota(user_id=current_user.id, estimated_tokens=2000)
        _check_quota_status(qs, qm, current_user.id)

        logger.info(f"Generating titles for user {current_user.id}: topic={request.topic!r}")

        # Call AI service — returns a plain dict
        raw = await ai_service.generate_titles(
            user_id=current_user.id,
            topic=request.topic,
            keywords=request.keywords or [],
            tone=request.tone or "engaging",
            target_audience=request.target_audience,  # Optional[str] — service accepts None
            count=request.count,
            use_cache=True
        )

        # Build Pydantic response from raw dict
        # AI service returns: {"titles": [{"title": ..., "seo_score": ..., "reasoning": ...}], ...}
        title_objects = [
            GeneratedTitle(
                text=t.get("title", ""),
                score=int(t.get("seo_score", 0)),
                reasoning=t.get("reasoning", "")
            )
            for t in (raw.get("titles") or [])
        ]

        response = GeneratedTitles(
            titles=title_objects,
            topic=request.topic,
            keywords=request.keywords or [],
            generated_at=_now()
        )

        # Record quota usage AFTER successful generation
        quota_manager.record_request(user_id=current_user.id, tokens_used=2000)

        # Save to history (fire-and-forget style — don't fail the request if this errors)
        try:
            await content_service.save_generated_content(
                user_id=current_user.id,
                content_type="title",
                content=raw,
                video_id=request.video_id,
                prompt_used=f"Topic: {request.topic}"
            )
        except Exception as save_err:
            logger.warning(f"Failed to save title history: {save_err}")

        logger.info(f"Generated {len(title_objects)} titles for user {current_user.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        if _is_gemini_quota_error(e):
            _raise_gemini_quota_429(e, current_user.id)
        logger.error(f"Error generating titles for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate titles: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# DESCRIPTION GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/description", response_model=GeneratedDescription)
async def generate_description(
    request: DescriptionGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video description.
    Returns 429 when quota is exceeded.
    """
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        # Quota check
        qs, qm = await quota_manager.check_quota(user_id=current_user.id, estimated_tokens=3000)
        _check_quota_status(qs, qm, current_user.id)

        logger.info(f"Generating description for user {current_user.id}: topic={request.topic!r}")

        # Call AI service — returns a plain dict
        raw = await ai_service.generate_description(
            user_id=current_user.id,
            topic=request.topic,
            keywords=request.keywords or [],
            tone=request.tone or "engaging",
            include_cta=request.include_cta,
            include_timestamps=request.include_timestamps,
            use_cache=True
        )

        # Build Pydantic response
        # AI service returns: {"description": ..., "seo_tips": [...], ...}
        desc_text = raw.get("description", "")
        response = GeneratedDescription(
            description=desc_text,
            word_count=len(desc_text.split()),
            includes_timestamps=request.include_timestamps,
            includes_links=request.include_links,
            includes_cta=request.include_cta,
            seo_tips=raw.get("seo_tips") or [],
            generated_at=_now()
        )

        quota_manager.record_request(user_id=current_user.id, tokens_used=3000)

        try:
            await content_service.save_generated_content(
                user_id=current_user.id,
                content_type="description",
                content=raw,
                video_id=request.video_id,
                prompt_used=f"Topic: {request.topic}"
            )
        except Exception as save_err:
            logger.warning(f"Failed to save description history: {save_err}")

        logger.info(f"Generated description for user {current_user.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        if _is_gemini_quota_error(e):
            _raise_gemini_quota_429(e, current_user.id)
        logger.error(f"Error generating description for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate description: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAGS GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/tags", response_model=GeneratedTags)
async def generate_tags(
    request: TagsGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered video tags.
    Returns 429 when quota is exceeded.
    """
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        if not (1 <= request.count <= 30):
            raise HTTPException(status_code=400, detail="Count must be between 1 and 30")

        # Quota check
        qs, qm = await quota_manager.check_quota(user_id=current_user.id, estimated_tokens=1500)
        _check_quota_status(qs, qm, current_user.id)

        logger.info(f"Generating tags for user {current_user.id}: topic={request.topic!r}")

        # Call AI service — returns a plain dict
        raw = await ai_service.generate_tags(
            user_id=current_user.id,
            topic=request.topic,
            keywords=request.keywords or [],
            count=request.count,
            use_cache=True
        )

        # Build Pydantic response
        # AI service returns: {"all_tags": [...], "primary_tags": [...], ...}
        all_tags = raw.get("all_tags") or []
        tag_categories = {
            "primary":   raw.get("primary_tags")   or [],
            "secondary": raw.get("secondary_tags") or [],
            "long_tail": raw.get("long_tail_tags") or [],
            "broad":     raw.get("broad_tags")     or [],
        }

        response = GeneratedTags(
            tags=all_tags,
            tag_count=len(all_tags),
            tag_categories=tag_categories,
            generated_at=_now()
        )

        quota_manager.record_request(user_id=current_user.id, tokens_used=1500)

        try:
            await content_service.save_generated_content(
                user_id=current_user.id,
                content_type="tags",
                content=raw,
                video_id=request.video_id,
                prompt_used=f"Topic: {request.topic}"
            )
        except Exception as save_err:
            logger.warning(f"Failed to save tags history: {save_err}")

        logger.info(f"Generated {len(all_tags)} tags for user {current_user.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        if _is_gemini_quota_error(e):
            _raise_gemini_quota_429(e, current_user.id)
        logger.error(f"Error generating tags for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate tags: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# THUMBNAIL TEXT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/thumbnail-text", response_model=GeneratedThumbnailText)
async def generate_thumbnail_text(
    request: ThumbnailTextRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate thumbnail text suggestions."""
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        qs, qm = await quota_manager.check_quota(user_id=current_user.id, estimated_tokens=500)
        _check_quota_status(qs, qm, current_user.id)

        # Simple rule-based suggestions (no Gemini call — saves quota)
        topic_short = request.topic[:30].upper()
        suggestions = [
            ThumbnailTextSuggestion(text=topic_short, style="Bold", reasoning="Short, high-contrast text"),
            ThumbnailTextSuggestion(text=f"HOW TO {topic_short}", style="Outline", reasoning="How-to framing boosts CTR"),
            ThumbnailTextSuggestion(text=f"{topic_short}?", style="Shadow", reasoning="Question format creates curiosity"),
        ]

        return GeneratedThumbnailText(
            suggestions=suggestions,
            design_tips=[
                "Use max 3-4 words on the thumbnail",
                "High contrast between text and background",
                "Font size should be readable at 120×68px",
            ],
            generated_at=_now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating thumbnail text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail text: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# THUMBNAIL GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/thumbnail")
async def generate_thumbnail(
    request: ThumbnailGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered thumbnail image.
    Returns 429 when quota is exceeded.
    """
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        if len(request.topic) > 50:
            raise HTTPException(status_code=400, detail="Topic must be 50 characters or less")
        if not (1 <= request.count <= 5):
            raise HTTPException(status_code=400, detail="Count must be between 1 and 5")

        qs, qm = await quota_manager.check_quota(user_id=current_user.id, estimated_tokens=300)
        _check_quota_status(qs, qm, current_user.id)

        logger.info(f"Generating thumbnail for user {current_user.id}: topic={request.topic!r}")

        result = await nano_service.generate_thumbnail(
            topic=request.topic,
            title=request.title,
            style=request.style,
            color_scheme=request.color_scheme,
        )

        quota_manager.record_request(user_id=current_user.id, tokens_used=300)
        logger.info(f"Generated thumbnail for user {current_user.id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating thumbnail for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY & STATS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/history")
async def get_content_history(
    current_user: UserResponse = Depends(get_current_user),
    content_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's content generation history."""
    try:
        return await content_service.get_content_history(
            user_id=current_user.id,
            content_type=content_type,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error getting content history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content history")


@router.get("/history/{content_id}")
async def get_content_by_id(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get specific generated content by ID."""
    try:
        content = await content_service.get_content_by_id(
            content_id=content_id,
            user_id=current_user.id
        )
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content")


@router.delete("/history/{content_id}")
async def delete_content(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete generated content."""
    try:
        success = await content_service.delete_content(
            content_id=content_id,
            user_id=current_user.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"message": "Content deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete content")


@router.get("/stats")
async def get_content_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get content generation statistics and quota usage."""
    try:
        stats = await content_service.get_content_stats(user_id=current_user.id)
        quota_info = quota_manager.get_quota_info(current_user.id)
        return {"stats": stats, "quota": quota_info}
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
