"""
Caching Module
Implements caching for trending analysis, user preferences, and statistics
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from app.core.config import settings


logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for various data types"""
    
    def __init__(self):
        """Initialize cache manager"""
        self._cache: Dict[str, tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        if not settings.CACHE_ENABLED:
            return None
        
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # Check if expired
        if datetime.utcnow() > expiry:
            del self._cache[key]
            logger.debug(f"Cache expired for key: {key}")
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int
    ) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        if not settings.CACHE_ENABLED:
            return
        
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set for key: {key} (TTL: {ttl_seconds}s)")
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        total_keys = len(self._cache)
        expired_keys = 0
        
        for key, (_, expiry) in list(self._cache.items()):
            if datetime.utcnow() > expiry:
                expired_keys += 1
        
        return {
            "total_keys": total_keys,
            "expired_keys": expired_keys,
            "active_keys": total_keys - expired_keys
        }


class TrendingAnalysisCache:
    """Caches trending analysis results"""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize trending analysis cache"""
        self.cache = cache_manager
        self.ttl_seconds = settings.CACHE_TRENDING_TTL_HOURS * 3600
    
    def get_analysis(self, niche: str, region: str, category_id: Optional[str]) -> Optional[Dict]:
        """
        Get cached trending analysis
        
        Args:
            niche: Content niche
            region: Region code
            category_id: YouTube category ID
            
        Returns:
            Cached analysis or None
        """
        key = self._make_key(niche, region, category_id)
        return self.cache.get(key)
    
    def set_analysis(
        self,
        niche: str,
        region: str,
        category_id: Optional[str],
        analysis: Dict
    ) -> None:
        """
        Cache trending analysis
        
        Args:
            niche: Content niche
            region: Region code
            category_id: YouTube category ID
            analysis: Analysis data to cache
        """
        key = self._make_key(niche, region, category_id)
        self.cache.set(key, analysis, self.ttl_seconds)
    
    def invalidate_analysis(self, niche: str, region: str, category_id: Optional[str]) -> None:
        """
        Invalidate cached analysis
        
        Args:
            niche: Content niche
            region: Region code
            category_id: YouTube category ID
        """
        key = self._make_key(niche, region, category_id)
        self.cache.delete(key)
    
    @staticmethod
    def _make_key(niche: str, region: str, category_id: Optional[str]) -> str:
        """Create cache key"""
        category_part = f":{category_id}" if category_id else ""
        return f"trending_analysis:{niche}:{region}{category_part}"


class UserPreferencesCache:
    """Caches user preferences"""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize user preferences cache"""
        self.cache = cache_manager
        self.ttl_seconds = settings.CACHE_PREFERENCES_TTL_DAYS * 24 * 3600
    
    def get_preferences(self, user_id: str) -> Optional[Dict]:
        """
        Get cached user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            Cached preferences or None
        """
        key = f"user_preferences:{user_id}"
        return self.cache.get(key)
    
    def set_preferences(self, user_id: str, preferences: Dict) -> None:
        """
        Cache user preferences
        
        Args:
            user_id: User ID
            preferences: Preferences data to cache
        """
        key = f"user_preferences:{user_id}"
        self.cache.set(key, preferences, self.ttl_seconds)
    
    def invalidate_preferences(self, user_id: str) -> None:
        """
        Invalidate cached preferences
        
        Args:
            user_id: User ID
        """
        key = f"user_preferences:{user_id}"
        self.cache.delete(key)


class GenerationStatsCache:
    """Caches generation statistics"""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize generation stats cache"""
        self.cache = cache_manager
        self.ttl_seconds = settings.CACHE_STATS_TTL_HOURS * 3600
    
    def get_stats(self, user_id: str) -> Optional[Dict]:
        """
        Get cached generation statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Cached statistics or None
        """
        key = f"generation_stats:{user_id}"
        return self.cache.get(key)
    
    def set_stats(self, user_id: str, stats: Dict) -> None:
        """
        Cache generation statistics
        
        Args:
            user_id: User ID
            stats: Statistics data to cache
        """
        key = f"generation_stats:{user_id}"
        self.cache.set(key, stats, self.ttl_seconds)
    
    def invalidate_stats(self, user_id: str) -> None:
        """
        Invalidate cached statistics
        
        Args:
            user_id: User ID
        """
        key = f"generation_stats:{user_id}"
        self.cache.delete(key)


# Create singleton instances
cache_manager = CacheManager()
trending_analysis_cache = TrendingAnalysisCache(cache_manager)
user_preferences_cache = UserPreferencesCache(cache_manager)
generation_stats_cache = GenerationStatsCache(cache_manager)
