"""
Content Service
Handles storage and retrieval of generated content
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.core.supabase import get_supabase
from app.models.content import GeneratedContentResponse, ContentHistoryResponse


class ContentService:
    """Service for managing generated content storage"""
    
    async def save_generated_content(
        self,
        user_id: str,
        content_type: str,
        content: Dict,
        video_id: Optional[str] = None,
        prompt_used: Optional[str] = None
    ) -> GeneratedContentResponse:
        """
        Save generated content to database
        
        Args:
            user_id: User ID
            content_type: Type of content (title, description, tags, thumbnail_text)
            content: Generated content data
            video_id: Associated video ID (optional)
            prompt_used: Prompt used for generation (optional)
            
        Returns:
            GeneratedContentResponse with saved content
        """
        supabase = get_supabase()
        
        try:
            # Insert into generated_content table
            result = supabase.table("generated_content").insert({
                "user_id": user_id,
                "video_id": video_id,
                "content_type": content_type,
                "content": content,
                "prompt_used": prompt_used,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            if not result.data:
                raise Exception("Failed to save generated content")
            
            saved_content = result.data[0]
            
            return GeneratedContentResponse(
                id=saved_content["id"],
                user_id=saved_content["user_id"],
                video_id=saved_content.get("video_id"),
                content_type=saved_content["content_type"],
                content=saved_content["content"],
                prompt_used=saved_content.get("prompt_used"),
                created_at=datetime.fromisoformat(saved_content["created_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            raise Exception(f"Failed to save generated content: {str(e)}")
    
    async def get_user_content_history(
        self,
        user_id: str,
        content_type: Optional[str] = None,
        video_id: Optional[str] = None,
        limit: int = 50
    ) -> ContentHistoryResponse:
        """
        Get user's content generation history
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            video_id: Filter by video ID (optional)
            limit: Maximum number of results
            
        Returns:
            ContentHistoryResponse with history items
        """
        supabase = get_supabase()
        
        try:
            # Build query
            query = supabase.table("generated_content").select("*").eq("user_id", user_id)
            
            if content_type:
                query = query.eq("content_type", content_type)
            
            if video_id:
                query = query.eq("video_id", video_id)
            
            # Execute query with limit and ordering
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            items = [
                GeneratedContentResponse(
                    id=item["id"],
                    user_id=item["user_id"],
                    video_id=item.get("video_id"),
                    content_type=item["content_type"],
                    content=item["content"],
                    prompt_used=item.get("prompt_used"),
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                )
                for item in result.data
            ]
            
            return ContentHistoryResponse(
                total_count=len(items),
                items=items
            )
            
        except Exception as e:
            raise Exception(f"Failed to get content history: {str(e)}")
    
    async def get_content_by_id(
        self,
        content_id: str,
        user_id: str
    ) -> Optional[GeneratedContentResponse]:
        """
        Get specific generated content by ID
        
        Args:
            content_id: Content ID
            user_id: User ID (for authorization)
            
        Returns:
            GeneratedContentResponse or None
        """
        supabase = get_supabase()
        
        try:
            result = supabase.table("generated_content").select("*").eq("id", content_id).eq("user_id", user_id).execute()
            
            if not result.data:
                return None
            
            item = result.data[0]
            
            return GeneratedContentResponse(
                id=item["id"],
                user_id=item["user_id"],
                video_id=item.get("video_id"),
                content_type=item["content_type"],
                content=item["content"],
                prompt_used=item.get("prompt_used"),
                created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            raise Exception(f"Failed to get content: {str(e)}")
    
    async def delete_content(
        self,
        content_id: str,
        user_id: str
    ) -> bool:
        """
        Delete generated content
        
        Args:
            content_id: Content ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted successfully
        """
        supabase = get_supabase()
        
        try:
            result = supabase.table("generated_content").delete().eq("id", content_id).eq("user_id", user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete content: {str(e)}")
    
    async def get_content_stats(
        self,
        user_id: str
    ) -> Dict:
        """
        Get user's content generation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        supabase = get_supabase()
        
        try:
            # Get all user's generated content
            result = supabase.table("generated_content").select("content_type, created_at").eq("user_id", user_id).execute()
            
            items = result.data
            
            # Calculate statistics
            stats = {
                "total_generated": len(items),
                "by_type": {
                    "title": 0,
                    "description": 0,
                    "tags": 0,
                    "thumbnail_text": 0
                },
                "recent_count": 0
            }
            
            # Count by type
            for item in items:
                content_type = item["content_type"]
                if content_type in stats["by_type"]:
                    stats["by_type"][content_type] += 1
                
                # Count recent (last 7 days)
                created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                days_ago = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
                if days_ago <= 7:
                    stats["recent_count"] += 1
            
            return stats
            
        except Exception as e:
            raise Exception(f"Failed to get content stats: {str(e)}")
    
    # ==================== Generator Feature Methods ====================
    
    async def save_batch_generation(
        self,
        user_id: str,
        topic: str,
        keywords: Optional[List[str]] = None,
        tone: str = "professional",
        target_audience: Optional[str] = None,
        video_length: Optional[str] = None
    ) -> str:
        """
        Save a batch generation record
        
        Args:
            user_id: User ID
            topic: Video topic
            keywords: List of keywords
            tone: Content tone
            target_audience: Target audience
            video_length: Video length
            
        Returns:
            Batch ID
        """
        supabase = get_supabase()
        
        try:
            result = supabase.table("generation_batches").insert({
                "user_id": user_id,
                "batch_type": "batch",
                "topic": topic,
                "keywords": keywords or [],
                "tone": tone,
                "target_audience": target_audience,
                "video_length": video_length,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            if not result.data:
                raise Exception("Failed to save batch generation")
            
            return result.data[0]["id"]
            
        except Exception as e:
            raise Exception(f"Failed to save batch generation: {str(e)}")
    
    async def save_generated_content_with_batch(
        self,
        user_id: str,
        content_type: str,
        content: Dict,
        batch_id: Optional[str] = None,
        quality_score: Optional[float] = None,
        video_id: Optional[str] = None,
        prompt_used: Optional[str] = None
    ) -> str:
        """
        Save generated content with batch association
        
        Args:
            user_id: User ID
            content_type: Type of content
            content: Generated content data
            batch_id: Associated batch ID
            quality_score: Quality score (0-100)
            video_id: Associated video ID
            prompt_used: Prompt used for generation
            
        Returns:
            Content ID
        """
        supabase = get_supabase()
        
        try:
            result = supabase.table("generated_content").insert({
                "user_id": user_id,
                "content_type": content_type,
                "content": content,
                "batch_id": batch_id,
                "quality_score": quality_score,
                "video_id": video_id,
                "prompt_used": prompt_used,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            if not result.data:
                raise Exception("Failed to save generated content")
            
            return result.data[0]["id"]
            
        except Exception as e:
            raise Exception(f"Failed to save generated content: {str(e)}")
    
    async def get_generation_history(
        self,
        user_id: str,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Get user's generation history with pagination
        
        Args:
            user_id: User ID
            content_type: Filter by content type
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Dictionary with total count and items
        """
        supabase = get_supabase()
        
        try:
            # Get total count
            count_query = supabase.table("generated_content").select("id", count="exact").eq("user_id", user_id)
            
            if content_type:
                count_query = count_query.eq("content_type", content_type)
            
            count_result = count_query.execute()
            total_count = count_result.count
            
            # Get paginated results
            query = supabase.table("generated_content").select("*").eq("user_id", user_id)
            
            if content_type:
                query = query.eq("content_type", content_type)
            
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            items = result.data or []
            
            return {
                "total_count": total_count,
                "items": items,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            raise Exception(f"Failed to get generation history: {str(e)}")
    
    async def save_user_preferences(
        self,
        user_id: str,
        preferred_tone: Optional[str] = None,
        preferred_keywords: Optional[List[str]] = None,
        preferred_audience: Optional[str] = None
    ) -> bool:
        """
        Save or update user generation preferences
        
        Args:
            user_id: User ID
            preferred_tone: Preferred tone
            preferred_keywords: Preferred keywords
            preferred_audience: Preferred audience
            
        Returns:
            True if successful
        """
        supabase = get_supabase()
        
        try:
            # Check if preferences exist
            existing = supabase.table("user_generation_preferences").select("id").eq("user_id", user_id).execute()
            
            if existing.data:
                # Update existing
                supabase.table("user_generation_preferences").update({
                    "preferred_tone": preferred_tone,
                    "preferred_keywords": preferred_keywords or [],
                    "preferred_audience": preferred_audience,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).execute()
            else:
                # Insert new
                supabase.table("user_generation_preferences").insert({
                    "user_id": user_id,
                    "preferred_tone": preferred_tone,
                    "preferred_keywords": preferred_keywords or [],
                    "preferred_audience": preferred_audience,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to save user preferences: {str(e)}")
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict]:
        """
        Get user generation preferences
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences or None
        """
        supabase = get_supabase()
        
        try:
            result = supabase.table("user_generation_preferences").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                return None
            
            return result.data[0]
            
        except Exception as e:
            raise Exception(f"Failed to get user preferences: {str(e)}")
    
    async def track_generation_history(
        self,
        user_id: str,
        content_id: str,
        action: str,
        content_type: str,
        quality_score: Optional[float] = None
    ) -> bool:
        """
        Track generation activity in history
        
        Args:
            user_id: User ID
            content_id: Content ID
            action: Action performed (generated, regenerated, edited, deleted)
            content_type: Type of content
            quality_score: Quality score
            
        Returns:
            True if successful
        """
        supabase = get_supabase()
        
        try:
            supabase.table("generation_history").insert({
                "user_id": user_id,
                "content_id": content_id,
                "action": action,
                "content_type": content_type,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to track generation history: {str(e)}")
    
    async def update_stats_cache(
        self,
        user_id: str,
        total_generations: int,
        by_type: Dict,
        avg_quality_score: float,
        most_used_keywords: List[str],
        most_used_tones: List[str],
        generation_trends: Dict
    ) -> bool:
        """
        Update generation statistics cache
        
        Args:
            user_id: User ID
            total_generations: Total generation count
            by_type: Count by content type
            avg_quality_score: Average quality score
            most_used_keywords: Most used keywords
            most_used_tones: Most used tones
            generation_trends: Generation trends by date
            
        Returns:
            True if successful
        """
        supabase = get_supabase()
        
        try:
            # Check if cache exists
            existing = supabase.table("generation_stats_cache").select("id").eq("user_id", user_id).execute()
            
            cache_data = {
                "total_generations": total_generations,
                "by_type": by_type,
                "avg_quality_score": avg_quality_score,
                "most_used_keywords": most_used_keywords,
                "most_used_tones": most_used_tones,
                "generation_trends": generation_trends,
                "cached_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            if existing.data:
                # Update existing
                supabase.table("generation_stats_cache").update(cache_data).eq("user_id", user_id).execute()
            else:
                # Insert new
                cache_data["user_id"] = user_id
                supabase.table("generation_stats_cache").insert(cache_data).execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to update stats cache: {str(e)}")


# Create singleton instance
content_service = ContentService()
