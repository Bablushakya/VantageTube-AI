"""
Content Service
Handles storage and retrieval of generated content
"""

from typing import List, Optional, Dict
from datetime import datetime
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


# Create singleton instance
content_service = ContentService()
