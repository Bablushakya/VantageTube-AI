"""
VantageTube AI - Supabase Client
Handles connection to Supabase for database and authentication
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional


class SupabaseClient:
    """Singleton Supabase client wrapper"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            cls._instance = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
        return cls._instance
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """Get Supabase client with service role key (admin access)"""
        return create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY
        )


# Convenience function to get client
def get_supabase() -> Client:
    """Get Supabase client instance"""
    return SupabaseClient.get_client()


# Convenience function to get admin client
def get_supabase_admin() -> Client:
    """Get Supabase admin client instance"""
    return SupabaseClient.get_admin_client()
