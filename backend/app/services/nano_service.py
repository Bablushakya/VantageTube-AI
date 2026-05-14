"""
VantageTube AI - Nano API Service
Handles AI-powered thumbnail generation using Nano API
"""

import json
import asyncio
import aiohttp
from typing import List, Dict, Optional
from app.core.config import settings
from app.services.thumbnail_template import ThumbnailTemplateBuilder
from app.services.thumbnail_composer import ThumbnailComposer


class NanoService:
    """Service for Nano API thumbnail generation"""
    
    def __init__(self):
        """Initialize Nano service"""
        self.api_key = settings.NANO_API_KEY
        # Real Nano API endpoint
        self.base_url = "https://api.nanoai.com/v1"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests to avoid rate limiting
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    async def generate_thumbnail(
        self,
        topic: str,
        title: Optional[str] = None,
        style: str = "modern",
        color_scheme: str = "vibrant",
        include_text: bool = True
    ) -> Dict:
        """
        Generate thumbnail using Nano API with structured template
        
        Args:
            topic: Video topic/subject (ONLY the topic, not a full prompt)
            title: Video title for context (optional)
            style: Thumbnail style (modern, retro, minimalist, bold)
            color_scheme: Color scheme (vibrant, dark, light, pastel)
            include_text: Include text overlay
            
        Returns:
            Dictionary with thumbnail URL and metadata
        """
        if not self.api_key:
            # Return error state if no API key
            return self._generate_error_response("API key not configured")
        
        # Apply rate limiting
        await self._rate_limit()
        
        try:
            # Step 1: Build structured template from topic
            template = ThumbnailTemplateBuilder.build_template(
                topic=topic,
                style=style,
                color_scheme=color_scheme
            )
            
            # Step 2: Convert template to image generation prompt
            prompt = ThumbnailTemplateBuilder.template_to_prompt(template)
            
            # Step 3: Call real Nano API with Flux Pro model
            base_image_url = await self._call_nano_api(prompt)
            
            if not base_image_url:
                return self._generate_error_response("Failed to generate base image")
            
            # Step 4: Add text overlay and elements
            if include_text:
                composition = ThumbnailComposer.compose_final_thumbnail(
                    base_image_url=base_image_url,
                    text=topic[:40],
                    style=style,
                    color_scheme=color_scheme,
                    add_elements=True
                )
                
                # Use final thumbnail if composition succeeded, otherwise use base
                final_url = composition.get("final_thumbnail_url", base_image_url)
            else:
                final_url = base_image_url
            
            # Step 5: Return successful response
            return {
                "thumbnail_url": final_url,
                "design_tips": [
                    f"✓ Generated with {style} style",
                    f"✓ Applied {color_scheme} color scheme",
                    "✓ Optimized for YouTube (1280x720px)",
                    "✓ High contrast and eye-catching",
                    "✓ Professional cinematic composition",
                    "✓ Ready for upload"
                ],
                "color_palette": template.colors,
                "style": style,
                "model": "flux-pro",
                "generated": True,
                "status": "success",
                "template": template.to_dict()
            }
        
        except asyncio.TimeoutError:
            print(f"Nano API timeout for topic: {topic}")
            return self._generate_error_response("Generation timeout - API took too long")
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return self._generate_error_response(f"Generation failed: {str(e)}")
    
    async def _call_nano_api(self, prompt: str) -> Optional[str]:
        """
        Call the real Nano API to generate base image
        
        Args:
            prompt: Structured image generation prompt
            
        Returns:
            Image URL or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "flux-pro",
                    "prompt": prompt,
                    "width": 1280,
                    "height": 720,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "seed": hash(prompt) % 1000000
                }
                
                async with session.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        image_url = data.get("image_url") or data.get("url") or data.get("output", [None])[0]
                        return image_url
                    else:
                        error_text = await response.text()
                        print(f"Nano API error ({response.status}): {error_text}")
                        return None
        
        except asyncio.TimeoutError:
            print("Nano API timeout")
            return None
        except Exception as e:
            print(f"Error calling Nano API: {e}")
            return None
    
    def _generate_error_response(self, error_message: str) -> Dict:
        """
        Generate a proper error response
        
        Args:
            error_message: Error message to include
            
        Returns:
            Error response dictionary
        """
        return {
            "thumbnail_url": None,
            "status": "error",
            "error": error_message,
            "generated": False,
            "design_tips": [
                "❌ Thumbnail generation failed",
                f"Reason: {error_message}",
                "Please try again or contact support"
            ],
            "color_palette": [],
            "style": None,
            "model": "flux-pro"
        }
    
    def _build_prompt(self, topic: str, title: str, style: str, color_scheme: str) -> str:
        """Build a detailed prompt for thumbnail generation - DEPRECATED"""
        # This method is deprecated. Use ThumbnailTemplateBuilder instead.
        return ""
    
    def _get_color_palette(self, color_scheme: str) -> List[str]:
        """Get color palette for the given scheme"""
        color_palettes = {
            "vibrant": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"],
            "dark": ["#1A1A1A", "#2D2D2D", "#404040", "#555555"],
            "light": ["#F5F5F5", "#E8E8E8", "#D0D0D0", "#B8B8B8"],
            "pastel": ["#FFB3BA", "#FFCCCB", "#FFFFBA", "#BAE1FF"]
        }
        return color_palettes.get(color_scheme, color_palettes['vibrant'])
    
    def _generate_mock_thumbnail(self, topic: str, style: str, color_scheme: str) -> Dict:
        """Generate mock thumbnail data for testing/fallback - DEPRECATED"""
        # This method is deprecated. Use _generate_error_response instead.
        return self._generate_error_response("Mock generation - API not available")
    
    async def generate_multiple_thumbnails(
        self,
        topic: str,
        title: Optional[str] = None,
        count: int = 3,
        styles: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate multiple thumbnail variations
        
        Args:
            topic: Video topic/subject
            title: Video title
            count: Number of variations
            styles: List of styles to try
            
        Returns:
            Dictionary with multiple thumbnail options
        """
        if not self.api_key:
            raise Exception("Nano API key not configured")
        
        if styles is None:
            styles = ["modern", "bold", "minimalist"]
        
        thumbnails = []
        
        for i, style in enumerate(styles[:count]):
            try:
                thumbnail = await self.generate_thumbnail(
                    topic=topic,
                    title=title,
                    style=style
                )
                thumbnails.append(thumbnail)
            except Exception as e:
                print(f"Error generating thumbnail with style {style}: {e}")
                # Add mock thumbnail on error
                thumbnails.append(self._generate_mock_thumbnail(topic, style, "vibrant"))
        
        return {
            "thumbnails": thumbnails,
            "count": len(thumbnails),
            "topic": topic,
            "title": title
        }
    
    async def optimize_thumbnail(
        self,
        thumbnail_url: str,
        optimization_type: str = "contrast"
    ) -> Dict:
        """
        Optimize existing thumbnail
        
        Args:
            thumbnail_url: URL of thumbnail to optimize
            optimization_type: Type of optimization (contrast, brightness, saturation, clarity)
            
        Returns:
            Dictionary with optimized thumbnail URL
        """
        if not self.api_key:
            raise Exception("Nano API key not configured")
        
        # Apply rate limiting
        await self._rate_limit()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "image_url": thumbnail_url,
                "optimization_type": optimization_type,
                "quality": "high"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/optimize",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Nano API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "optimized_url": data.get("url"),
                        "optimization_type": optimization_type,
                        "improvements": data.get("improvements", [])
                    }
        
        except Exception as e:
            print(f"Error optimizing thumbnail: {e}")
            raise


# Create singleton instance
nano_service = NanoService()
