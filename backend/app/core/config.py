"""
VantageTube AI - Configuration Settings
Handles all environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Info
    APP_NAME: str = "VantageTube AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # YouTube API Configuration
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/auth/youtube/callback"
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = ""
    
    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500"
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_GENERATIONS_PER_DAY: int = 100
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Caching Configuration
    CACHE_ENABLED: bool = True
    CACHE_TRENDING_TTL_HOURS: int = 1
    CACHE_PREFERENCES_TTL_DAYS: int = 7
    CACHE_STATS_TTL_HOURS: int = 24
    
    # Database Connection Pooling
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Performance Targets (in seconds)
    TITLE_GENERATION_TIMEOUT: int = 5
    DESCRIPTION_GENERATION_TIMEOUT: int = 8
    TAG_GENERATION_TIMEOUT: int = 5
    THUMBNAIL_GENERATION_TIMEOUT: int = 5
    BATCH_GENERATION_TIMEOUT: int = 30
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


# Create global settings instance
settings = Settings()
