"""
Rate Limiting Module
Implements rate limiting for API endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.core.supabase import get_supabase
from app.core.config import settings


logger = logging.getLogger(__name__)


class RateLimiter:
    """Implements rate limiting for API endpoints"""
    
    def __init__(self):
        """Initialize rate limiter"""
        self._memory_cache = {}  # In-memory cache for fast lookups
    
    async def check_rate_limit(
        self,
        user_id: str,
        limit_type: str = "generations_per_day"
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User ID
            limit_type: Type of rate limit (generations_per_day, requests_per_minute)
            
        Returns:
            Tuple of (allowed, message)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, None
        
        try:
            if limit_type == "generations_per_day":
                return await self._check_daily_generation_limit(user_id)
            elif limit_type == "requests_per_minute":
                return await self._check_minute_request_limit(user_id)
            else:
                return True, None
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Allow request if rate limiter fails
            return True, None
    
    async def _check_daily_generation_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check daily generation limit"""
        try:
            supabase = get_supabase()
            
            # Get today's generation count
            today = datetime.utcnow().date()
            result = supabase.table("generation_history").select(
                "count"
            ).eq("user_id", user_id).gte(
                "timestamp",
                f"{today}T00:00:00Z"
            ).execute()
            
            generation_count = len(result.data) if result.data else 0
            
            if generation_count >= settings.RATE_LIMIT_GENERATIONS_PER_DAY:
                message = (
                    f"Rate limit exceeded. You have generated "
                    f"{generation_count}/{settings.RATE_LIMIT_GENERATIONS_PER_DAY} "
                    f"items today. Please try again tomorrow."
                )
                logger.warning(f"Rate limit exceeded for user {user_id}: {generation_count} generations")
                return False, message
            
            return True, None
        except Exception as e:
            logger.error(f"Error checking daily generation limit: {str(e)}")
            return True, None
    
    async def _check_minute_request_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check per-minute request limit"""
        try:
            # Check memory cache first
            cache_key = f"rate_limit:{user_id}:minute"
            now = datetime.utcnow()
            
            if cache_key in self._memory_cache:
                last_reset, count = self._memory_cache[cache_key]
                
                # Reset if minute has passed
                if (now - last_reset).total_seconds() >= 60:
                    self._memory_cache[cache_key] = (now, 1)
                    return True, None
                
                # Check limit
                if count >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
                    message = (
                        f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} "
                        f"requests per minute. Please try again in a moment."
                    )
                    logger.warning(f"Per-minute rate limit exceeded for user {user_id}")
                    return False, message
                
                # Increment count
                self._memory_cache[cache_key] = (last_reset, count + 1)
            else:
                self._memory_cache[cache_key] = (now, 1)
            
            return True, None
        except Exception as e:
            logger.error(f"Error checking per-minute request limit: {str(e)}")
            return True, None
    
    async def record_generation(
        self,
        user_id: str,
        content_type: str,
        success: bool
    ) -> None:
        """
        Record a generation for rate limiting purposes
        
        Args:
            user_id: User ID
            content_type: Type of content generated
            success: Whether generation was successful
        """
        try:
            supabase = get_supabase()
            
            supabase.table("generation_history").insert({
                "user_id": user_id,
                "content_type": content_type,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error recording generation: {str(e)}")
    
    def get_remaining_generations(self, user_id: str) -> int:
        """
        Get remaining generations for user today
        
        Args:
            user_id: User ID
            
        Returns:
            Number of remaining generations
        """
        try:
            supabase = get_supabase()
            
            # Get today's generation count
            today = datetime.utcnow().date()
            result = supabase.table("generation_history").select(
                "count"
            ).eq("user_id", user_id).gte(
                "timestamp",
                f"{today}T00:00:00Z"
            ).execute()
            
            generation_count = len(result.data) if result.data else 0
            remaining = max(0, settings.RATE_LIMIT_GENERATIONS_PER_DAY - generation_count)
            
            return remaining
        except Exception as e:
            logger.error(f"Error getting remaining generations: {str(e)}")
            return settings.RATE_LIMIT_GENERATIONS_PER_DAY


# Create singleton instance
rate_limiter = RateLimiter()
