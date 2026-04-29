"""
VantageTube AI - Storage Service
Handles file uploads to Supabase Storage
"""

from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.core.supabase import get_supabase
import uuid
import os


class StorageService:
    """Service for handling file uploads"""
    
    BUCKET_NAME = "avatars"
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    async def upload_avatar(user_id: str, file: UploadFile) -> str:
        """
        Upload user avatar to Supabase Storage
        
        Args:
            user_id: User ID
            file: Uploaded file
            
        Returns:
            Public URL of uploaded avatar
            
        Raises:
            HTTPException: If upload fails
        """
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in StorageService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(StorageService.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > StorageService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {StorageService.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        supabase = get_supabase()
        
        try:
            # Generate unique filename
            filename = f"{user_id}/{uuid.uuid4()}{file_ext}"
            
            # Upload to Supabase Storage
            response = supabase.storage.from_(StorageService.BUCKET_NAME).upload(
                filename,
                content,
                {
                    "content-type": file.content_type,
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = supabase.storage.from_(StorageService.BUCKET_NAME).get_public_url(filename)
            
            # Update user avatar_url in database
            supabase.table("users").update({"avatar_url": public_url}).eq("id", user_id).execute()
            
            return public_url
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload avatar: {str(e)}"
            )
    
    @staticmethod
    async def delete_avatar(user_id: str, avatar_url: str) -> dict:
        """
        Delete user avatar from Supabase Storage
        
        Args:
            user_id: User ID
            avatar_url: Avatar URL to delete
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If deletion fails
        """
        supabase = get_supabase()
        
        try:
            # Extract filename from URL
            # URL format: https://[project].supabase.co/storage/v1/object/public/avatars/[filename]
            filename = avatar_url.split(f"/{StorageService.BUCKET_NAME}/")[-1]
            
            # Delete from storage
            supabase.storage.from_(StorageService.BUCKET_NAME).remove([filename])
            
            # Update user avatar_url to null
            supabase.table("users").update({"avatar_url": None}).eq("id", user_id).execute()
            
            return {"message": "Avatar deleted successfully"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete avatar: {str(e)}"
            )
