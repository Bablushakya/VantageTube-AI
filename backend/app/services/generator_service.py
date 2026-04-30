"""
AI Content Generator Service
Orchestrates content generation workflow
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
from app.services.trending_service import trending_service
from app.services.ai_service import ai_service
from app.services.content_service import content_service
from app.services.analysis_service import analysis_service
from app.core.supabase import get_supabase
from app.core.rate_limiter import rate_limiter
from app.core.cache import (
    trending_analysis_cache,
    user_preferences_cache,
    generation_stats_cache
)
from app.utils.validation import validator, scorer, regeneration_logic
from app.utils.monitoring import (
    performance_metrics,
    activity_audit_trail,
    error_logger
)
from app.models.generator import (
    AnalysisRequest, AnalysisResponse, ContentPattern,
    GenerationRequest, TitleGenerationRequest, DescriptionGenerationRequest,
    TagsGenerationRequest, ThumbnailTextRequest, BatchGenerationRequest,
    BatchGenerationResponse, GeneratedContent, GenerationStats
)
from app.models.content import (
    GeneratedTitles, GeneratedTags, GeneratedDescription, GeneratedThumbnailText
)


logger = logging.getLogger(__name__)


class GeneratorService:
    """Service for orchestrating AI content generation"""
    
    def __init__(self):
        """Initialize generator service"""
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 3600  # 1 hour
    
    async def analyze_niche(
        self,
        request: AnalysisRequest
    ) -> AnalysisResponse:
        """
        Analyze trending videos in a niche
        
        Args:
            request: Analysis request with niche, region, category
            
        Returns:
            AnalysisResponse with patterns and opportunities
        """
        try:
            # Check cache first
            cached_analysis = trending_analysis_cache.get_analysis(
                request.niche,
                request.region,
                request.category_id
            )
            if cached_analysis:
                logger.info(f"Using cached analysis for {request.niche}")
                return cached_analysis
            
            # Fetch trending videos
            logger.info(f"Fetching trending videos for niche: {request.niche}")
            videos = await trending_service.get_trending_videos(
                keywords=[request.niche],
                category_id=request.category_id,
                region=request.region,
                limit=request.limit
            )
            
            if not videos:
                logger.warning(f"No trending videos found for niche: {request.niche}")
                raise Exception(f"No trending data available for niche: {request.niche}")
            
            # Extract patterns
            logger.info(f"Extracting patterns from {len(videos)} videos")
            patterns = await analysis_service.extract_content_patterns(videos)
            
            # Identify title patterns
            title_patterns = await analysis_service.identify_title_patterns(videos)
            
            # Identify opportunities
            opportunities = await analysis_service.identify_opportunities(videos, patterns)
            
            # Calculate aggregate metrics
            avg_viral_score = sum(v.viral_score for v in videos) / len(videos) if videos else 0
            avg_engagement_rate = sum(v.engagement_rate for v in videos) / len(videos) if videos else 0
            
            # Convert patterns to list
            top_keywords = sorted(
                patterns.values(),
                key=lambda x: x.frequency,
                reverse=True
            )[:10]
            
            response = AnalysisResponse(
                top_keywords=top_keywords,
                common_title_patterns=title_patterns[:5],
                avg_viral_score=round(avg_viral_score, 2),
                avg_engagement_rate=round(avg_engagement_rate, 2),
                total_videos_analyzed=len(videos),
                opportunities=opportunities
            )
            
            # Cache the response
            trending_analysis_cache.set_analysis(
                request.niche,
                request.region,
                request.category_id,
                response
            )
            
            logger.info(f"Analysis complete for {request.niche}")
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing niche {request.niche}: {str(e)}")
            raise
    
    async def generate_titles(
        self,
        user_id: str,
        request: TitleGenerationRequest
    ) -> GeneratedTitles:
        """
        Generate optimized titles
        
        Args:
            user_id: User ID
            request: Title generation request
            
        Returns:
            GeneratedTitles with multiple title options
        """
        start_time = datetime.utcnow()
        try:
            logger.info(f"Generating {request.count} titles for user {user_id}")
            
            # Check rate limit
            allowed, message = await rate_limiter.check_rate_limit(user_id, "generations_per_day")
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                raise Exception(message)
            
            # Call AI service
            titles_response = await ai_service.generate_titles(
                topic=request.topic,
                keywords=request.keywords or [],
                tone=request.tone,
                target_audience=request.target_audience,
                count=request.count
            )
            
            # Validate and score titles
            validated_titles = []
            for title in titles_response.titles:
                is_valid, validation_details = validator.validate_title(
                    title.text,
                    request.keywords
                )
                
                # Calculate quality score
                quality_score = scorer.calculate_title_quality_score(
                    title.text,
                    request.keywords
                )
                
                # Add score to title
                title.score = quality_score
                
                if is_valid or quality_score >= 60:
                    validated_titles.append(title)
                else:
                    logger.warning(f"Title validation failed: {title.text}")
            
            # If validation failed for most titles, regenerate
            if len(validated_titles) < request.count * 0.8:
                logger.warning(f"Title validation failed, regenerating")
                titles_response = await ai_service.generate_titles(
                    topic=request.topic,
                    keywords=request.keywords or [],
                    tone=request.tone,
                    target_audience=request.target_audience,
                    count=request.count
                )
                validated_titles = titles_response.titles
            else:
                titles_response.titles = validated_titles
            
            # Save to database
            for title in validated_titles:
                await content_service.save_generated_content(
                    user_id=user_id,
                    content_type="title",
                    content=title.dict(),
                    prompt_used=f"Topic: {request.topic}, Tone: {request.tone}"
                )
            
            # Record generation for rate limiting
            await rate_limiter.record_generation(user_id, "title", True)
            
            # Log performance metrics
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            avg_score = sum(t.score for t in validated_titles) / len(validated_titles) if validated_titles else 0
            performance_metrics.log_generation_metrics(
                user_id=user_id,
                content_type="title",
                generation_time_ms=elapsed_ms,
                quality_score=avg_score,
                success=True
            )
            
            # Log activity
            activity_audit_trail.log_activity(
                user_id=user_id,
                action="generated",
                resource_type="title",
                details={"count": len(validated_titles), "topic": request.topic}
            )
            
            logger.info(f"Generated {len(validated_titles)} titles for user {user_id}")
            return titles_response
            
        except Exception as e:
            logger.error(f"Error generating titles: {str(e)}")
            
            # Log error
            error_id = error_logger.log_error(
                user_id=user_id,
                endpoint="/api/generator/titles",
                error_type="TitleGenerationError",
                error_message=str(e),
                context={"topic": request.topic}
            )
            
            # Log performance metrics for failure
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            performance_metrics.log_generation_metrics(
                user_id=user_id,
                content_type="title",
                generation_time_ms=elapsed_ms,
                quality_score=0,
                success=False
            )
            
            raise
    
    async def generate_tags(
        self,
        user_id: str,
        request: TagsGenerationRequest
    ) -> GeneratedTags:
        """
        Generate optimized tags
        
        Args:
            user_id: User ID
            request: Tags generation request
            
        Returns:
            GeneratedTags with categorized tags
        """
        try:
            logger.info(f"Generating {request.count} tags for user {user_id}")
            
            # Call AI service
            tags_response = await ai_service.generate_tags(
                topic=request.topic,
                title=request.title,
                keywords=request.keywords or [],
                count=request.count
            )
            
            # Validate tags
            is_valid, validation_details = validator.validate_tags(tags_response.tags, request.title)
            
            if not is_valid or validation_details.get("score", 0) < 60:
                logger.warning(f"Tag validation failed, regenerating")
                tags_response = await ai_service.generate_tags(
                    topic=request.topic,
                    title=request.title,
                    keywords=request.keywords or [],
                    count=request.count
                )
            
            # Save to database
            await content_service.save_generated_content(
                user_id=user_id,
                content_type="tags",
                content=tags_response.dict(),
                prompt_used=f"Topic: {request.topic}"
            )
            
            logger.info(f"Generated {len(tags_response.tags)} tags for user {user_id}")
            return tags_response
            
        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            raise
    
    async def generate_description(
        self,
        user_id: str,
        request: DescriptionGenerationRequest
    ) -> GeneratedDescription:
        """
        Generate optimized description
        
        Args:
            user_id: User ID
            request: Description generation request
            
        Returns:
            GeneratedDescription with optimized description
        """
        try:
            logger.info(f"Generating description for user {user_id}")
            
            # Call AI service
            description_response = await ai_service.generate_description(
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
            
            # Validate description
            is_valid, validation_details = validator.validate_description(
                description_response.description,
                request.keywords
            )
            
            if not is_valid or validation_details.get("score", 0) < 60:
                logger.warning(f"Description validation failed, regenerating")
                description_response = await ai_service.generate_description(
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
            
            # Save to database
            await content_service.save_generated_content(
                user_id=user_id,
                content_type="description",
                content=description_response.dict(),
                prompt_used=f"Topic: {request.topic}"
            )
            
            logger.info(f"Generated description for user {user_id}")
            return description_response
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            raise
    
    async def generate_thumbnail_text(
        self,
        user_id: str,
        request: ThumbnailTextRequest
    ) -> GeneratedThumbnailText:
        """
        Generate thumbnail text suggestions
        
        Args:
            user_id: User ID
            request: Thumbnail text request
            
        Returns:
            GeneratedThumbnailText with suggestions
        """
        try:
            logger.info(f"Generating {request.count} thumbnail text suggestions for user {user_id}")
            
            # Call AI service
            thumbnail_response = await ai_service.generate_thumbnail_text(
                topic=request.topic,
                title=request.title,
                count=request.count
            )
            
            # Validate thumbnail text
            validated_suggestions = []
            for suggestion in thumbnail_response.suggestions:
                is_valid, validation_details = validator.validate_thumbnail_text(suggestion.text)
                if is_valid or validation_details.get("score", 0) >= 60:
                    validated_suggestions.append(suggestion)
            
            if len(validated_suggestions) < request.count * 0.8:
                logger.warning(f"Thumbnail text validation failed, regenerating")
                thumbnail_response = await ai_service.generate_thumbnail_text(
                    topic=request.topic,
                    title=request.title,
                    count=request.count
                )
            else:
                thumbnail_response.suggestions = validated_suggestions
            
            # Save to database
            await content_service.save_generated_content(
                user_id=user_id,
                content_type="thumbnail_text",
                content=thumbnail_response.dict(),
                prompt_used=f"Topic: {request.topic}"
            )
            
            logger.info(f"Generated {len(thumbnail_response.suggestions)} thumbnail text suggestions for user {user_id}")
            return thumbnail_response
            
        except Exception as e:
            logger.error(f"Error generating thumbnail text: {str(e)}")
            raise
    
    async def generate_all(
        self,
        user_id: str,
        request: BatchGenerationRequest
    ) -> BatchGenerationResponse:
        """
        Generate all content types in batch
        
        Args:
            user_id: User ID
            request: Batch generation request
            
        Returns:
            BatchGenerationResponse with all content types
        """
        start_time = datetime.utcnow()
        try:
            logger.info(f"Starting batch generation for user {user_id}")
            batch_id = str(uuid.uuid4())
            
            # Check rate limit
            allowed, message = await rate_limiter.check_rate_limit(user_id, "generations_per_day")
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                raise Exception(message)
            
            # Create batch record
            supabase = get_supabase()
            supabase.table("generation_batches").insert({
                "id": batch_id,
                "user_id": user_id,
                "batch_type": "batch",
                "topic": request.topic,
                "keywords": request.keywords,
                "tone": request.tone,
                "target_audience": request.target_audience,
                "video_length": request.video_length,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Create request objects for parallel processing
            title_request = TitleGenerationRequest(
                topic=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                target_audience=request.target_audience,
                video_length=request.video_length,
                count=request.title_count
            )
            
            tags_request = TagsGenerationRequest(
                topic=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                target_audience=request.target_audience,
                video_length=request.video_length,
                count=request.tag_count
            )
            
            description_request = DescriptionGenerationRequest(
                topic=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                target_audience=request.target_audience,
                video_length=request.video_length,
                include_timestamps=request.include_timestamps,
                include_links=request.include_links,
                include_cta=request.include_cta
            )
            
            thumbnail_request = ThumbnailTextRequest(
                topic=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                target_audience=request.target_audience,
                video_length=request.video_length,
                count=request.thumbnail_count
            )
            
            # Generate all in parallel using asyncio
            logger.info("Starting parallel generation of all content types")
            titles, tags, description, thumbnail_text = await asyncio.gather(
                self.generate_titles(user_id, title_request),
                self.generate_tags(user_id, tags_request),
                self.generate_description(user_id, description_request),
                self.generate_thumbnail_text(user_id, thumbnail_request),
                return_exceptions=False
            )
            
            # Calculate quality scores
            quality_scores = scorer.calculate_batch_quality_score(
                titles=[t.dict() for t in titles.titles],
                tags=tags.dict(),
                description=description.dict(),
                thumbnail_texts=[s.dict() for s in thumbnail_text.suggestions]
            )
            
            response = BatchGenerationResponse(
                batch_id=batch_id,
                titles=[t.dict() for t in titles.titles],
                tags=tags.dict(),
                description=description.dict(),
                thumbnail_text=[s.dict() for s in thumbnail_text.suggestions],
                quality_scores=quality_scores
            )
            
            # Record batch generation for rate limiting
            await rate_limiter.record_generation(user_id, "batch", True)
            
            # Log performance metrics
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            avg_score = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0
            performance_metrics.log_generation_metrics(
                user_id=user_id,
                content_type="batch",
                generation_time_ms=elapsed_ms,
                quality_score=avg_score,
                success=True,
                batch_id=batch_id
            )
            
            # Log activity
            activity_audit_trail.log_activity(
                user_id=user_id,
                action="generated",
                resource_type="batch",
                resource_id=batch_id,
                details={
                    "topic": request.topic,
                    "title_count": request.title_count,
                    "tag_count": request.tag_count,
                    "thumbnail_count": request.thumbnail_count
                }
            )
            
            logger.info(f"Batch generation complete for user {user_id}, batch_id: {batch_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in batch generation: {str(e)}")
            
            # Log error
            error_id = error_logger.log_error(
                user_id=user_id,
                endpoint="/api/generator/generate-all",
                error_type="BatchGenerationError",
                error_message=str(e),
                context={"topic": request.topic}
            )
            
            # Log performance metrics for failure
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            performance_metrics.log_generation_metrics(
                user_id=user_id,
                content_type="batch",
                generation_time_ms=elapsed_ms,
                quality_score=0,
                success=False
            )
            
            raise
    
    async def get_generation_history(
        self,
        user_id: str,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[GeneratedContent]:
        """
        Retrieve user's generation history
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of generated content
        """
        try:
            logger.info(f"Retrieving generation history for user {user_id}")
            
            history = await content_service.get_user_content_history(
                user_id=user_id,
                content_type=content_type,
                limit=limit
            )
            
            return history.items
            
        except Exception as e:
            logger.error(f"Error retrieving generation history: {str(e)}")
            raise
    
    async def get_generation_stats(
        self,
        user_id: str
    ) -> GenerationStats:
        """
        Get user's generation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            GenerationStats with usage metrics
        """
        try:
            logger.info(f"Calculating generation stats for user {user_id}")
            
            # Check cache first
            cached_stats = generation_stats_cache.get_stats(user_id)
            if cached_stats:
                logger.info(f"Using cached stats for user {user_id}")
                return cached_stats
            
            supabase = get_supabase()
            
            # Get all user's generated content
            result = supabase.table("generated_content").select(
                "content_type, created_at"
            ).eq("user_id", user_id).execute()
            
            items = result.data
            
            # Calculate statistics
            by_type = {
                "title": 0,
                "tags": 0,
                "description": 0,
                "thumbnail_text": 0
            }
            
            generation_trends = {}
            total_quality_scores = []
            
            for item in items:
                content_type = item["content_type"]
                if content_type in by_type:
                    by_type[content_type] += 1
                
                # Track trends by date
                created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                date_key = created_at.strftime("%Y-%m-%d")
                generation_trends[date_key] = generation_trends.get(date_key, 0) + 1
            
            # Get most used keywords and tones from preferences
            pref_result = supabase.table("user_generation_preferences").select(
                "preferred_keywords, preferred_tone"
            ).eq("user_id", user_id).execute()
            
            most_used_keywords = []
            most_used_tones = []
            
            if pref_result.data:
                pref = pref_result.data[0]
                most_used_keywords = pref.get("preferred_keywords", [])[:5]
                most_used_tones = [pref.get("preferred_tone", "professional")]
            
            # Calculate average quality score
            avg_quality_score = sum(total_quality_scores) / len(total_quality_scores) if total_quality_scores else 0
            
            stats = GenerationStats(
                total_generations=len(items),
                by_type=by_type,
                avg_quality_score=round(avg_quality_score, 2),
                most_used_keywords=most_used_keywords,
                most_used_tones=most_used_tones,
                generation_trends=generation_trends,
                last_generation=datetime.utcnow() if items else None
            )
            
            # Cache the stats
            generation_stats_cache.set_stats(user_id, stats)
            
            logger.info(f"Stats calculated for user {user_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating generation stats: {str(e)}")
            raise


# Create singleton instance
generator_service = GeneratorService()
