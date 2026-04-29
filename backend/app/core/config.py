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
