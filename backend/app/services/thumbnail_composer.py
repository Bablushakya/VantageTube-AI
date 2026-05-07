"""
VantageTube AI - Thumbnail Composer
Handles post-generation thumbnail composition with text and overlays
"""

from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from urllib.request import urlopen
import asyncio


class ThumbnailComposer:
    """Composes final thumbnails by adding text and overlays to base images"""
    
    # Text overlay styles
    TEXT_STYLES = {
        "modern": {
            "font_size": 72,
            "font_weight": "bold",
            "text_color": (255, 255, 255),
            "shadow_color": (0, 0, 0),
            "shadow_offset": 3,
            "position": "bottom-center",
            "background": "semi-transparent-dark"
        },
        "bold": {
            "font_size": 80,
            "font_weight": "extra-bold",
            "text_color": (255, 255, 255),
            "shadow_color": (0, 0, 0),
            "shadow_offset": 4,
            "position": "center",
            "background": "solid-dark"
        },
        "minimalist": {
            "font_size": 48,
            "font_weight": "light",
            "text_color": (255, 255, 255),
            "shadow_color": (0, 0, 0),
            "shadow_offset": 2,
            "position": "top-right",
            "background": "none"
        },
        "retro": {
            "font_size": 64,
            "font_weight": "bold",
            "text_color": (255, 255, 0),
            "shadow_color": (0, 0, 0),
            "shadow_offset": 3,
            "position": "bottom-center",
            "background": "semi-transparent-dark"
        }
    }
    
    @staticmethod
    def add_text_overlay(
        image_url: str,
        text: str,
        style: str = "modern",
        color_scheme: str = "vibrant"
    ) -> Optional[str]:
        """
        Add text overlay to thumbnail image
        
        Args:
            image_url: URL of base thumbnail image
            text: Text to overlay
            style: Thumbnail style
            color_scheme: Color scheme
            
        Returns:
            Base64 encoded image with text overlay or None if failed
        """
        try:
            # Get text style
            text_style = ThumbnailComposer.TEXT_STYLES.get(style, ThumbnailComposer.TEXT_STYLES["modern"])
            
            # Download and open image
            response = urlopen(image_url, timeout=10)
            img = Image.open(response)
            img = img.convert('RGBA')
            
            # Create text layer
            txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # Prepare text
            text = text[:40]  # Limit to 40 characters
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            img_width, img_height = img.size
            
            # Position based on style
            if text_style["position"] == "bottom-center":
                x = (img_width - text_width) // 2
                y = img_height - text_height - 40
            elif text_style["position"] == "center":
                x = (img_width - text_width) // 2
                y = (img_height - text_height) // 2
            elif text_style["position"] == "top-right":
                x = img_width - text_width - 30
                y = 30
            else:
                x = (img_width - text_width) // 2
                y = img_height - text_height - 40
            
            # Add shadow
            shadow_offset = text_style["shadow_offset"]
            draw.text(
                (x + shadow_offset, y + shadow_offset),
                text,
                fill=(*text_style["shadow_color"], 200),
                font=None
            )
            
            # Add main text
            draw.text(
                (x, y),
                text,
                fill=(*text_style["text_color"], 255),
                font=None
            )
            
            # Composite layers
            img = Image.alpha_composite(img, txt_layer)
            img = img.convert('RGB')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
        
        except Exception as e:
            print(f"Error adding text overlay: {e}")
            return None
    
    @staticmethod
    def add_emphasis_elements(
        image_url: str,
        elements: List[str],
        style: str = "modern"
    ) -> Optional[str]:
        """
        Add emphasis elements (arrows, circles, badges) to thumbnail
        
        Args:
            image_url: URL of base thumbnail image
            elements: List of elements to add (arrow, circle, badge, highlight)
            style: Thumbnail style
            
        Returns:
            Base64 encoded image with elements or None if failed
        """
        try:
            # Download and open image
            response = urlopen(image_url, timeout=10)
            img = Image.open(response)
            img = img.convert('RGBA')
            
            # Create overlay layer
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            img_width, img_height = img.size
            
            # Add elements
            for element in elements:
                if element == "arrow":
                    # Draw arrow pointing to focal point
                    arrow_x = img_width - 100
                    arrow_y = 50
                    draw.polygon(
                        [(arrow_x, arrow_y), (arrow_x + 40, arrow_y + 30), (arrow_x + 20, arrow_y + 30)],
                        fill=(255, 255, 0, 200)
                    )
                
                elif element == "circle":
                    # Draw emphasis circle
                    circle_x = img_width - 80
                    circle_y = img_height - 80
                    radius = 40
                    draw.ellipse(
                        [(circle_x - radius, circle_y - radius), (circle_x + radius, circle_y + radius)],
                        outline=(255, 255, 0, 200),
                        width=3
                    )
                
                elif element == "badge":
                    # Draw badge
                    badge_x = 20
                    badge_y = 20
                    draw.rectangle(
                        [(badge_x, badge_y), (badge_x + 80, badge_y + 40)],
                        fill=(255, 0, 0, 200)
                    )
                
                elif element == "highlight":
                    # Draw highlight box
                    highlight_x = img_width // 2 - 100
                    highlight_y = img_height // 2 - 50
                    draw.rectangle(
                        [(highlight_x, highlight_y), (highlight_x + 200, highlight_y + 100)],
                        outline=(255, 255, 0, 200),
                        width=4
                    )
            
            # Composite layers
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
        
        except Exception as e:
            print(f"Error adding emphasis elements: {e}")
            return None
    
    @staticmethod
    def compose_final_thumbnail(
        base_image_url: str,
        text: str,
        style: str = "modern",
        color_scheme: str = "vibrant",
        add_elements: bool = True
    ) -> Dict:
        """
        Compose final thumbnail with text and optional elements
        
        Args:
            base_image_url: URL of base generated image
            text: Text to overlay
            style: Thumbnail style
            color_scheme: Color scheme
            add_elements: Whether to add emphasis elements
            
        Returns:
            Dictionary with final thumbnail URL and metadata
        """
        
        try:
            # Add text overlay
            with_text = ThumbnailComposer.add_text_overlay(
                base_image_url,
                text,
                style,
                color_scheme
            )
            
            if not with_text:
                # If text overlay fails, return base image
                return {
                    "success": True,
                    "final_thumbnail_url": base_image_url,
                    "base_image_url": base_image_url,
                    "text_added": False,
                    "elements_added": False,
                    "composition_layers": ["base_image"],
                    "note": "Text overlay skipped - returning base image"
                }
            
            # Add emphasis elements if requested
            final_image = with_text
            if add_elements:
                elements = ["arrow", "highlight"]
                with_elements = ThumbnailComposer.add_emphasis_elements(
                    with_text,
                    elements,
                    style
                )
                if with_elements:
                    final_image = with_elements
            
            return {
                "success": True,
                "final_thumbnail_url": final_image,
                "base_image_url": base_image_url,
                "text_added": True,
                "elements_added": add_elements,
                "composition_layers": ["base_image", "text_overlay", "emphasis_elements" if add_elements else None]
            }
        
        except Exception as e:
            print(f"Error composing thumbnail: {e}")
            # Return base image on error
            return {
                "success": True,
                "final_thumbnail_url": base_image_url,
                "base_image_url": base_image_url,
                "text_added": False,
                "elements_added": False,
                "composition_layers": ["base_image"],
                "note": f"Composition skipped due to error: {str(e)}"
            }
