"""
VantageTube AI - Thumbnail Template Builder
Converts video topics into structured thumbnail generation templates
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ThumbnailTemplate:
    """Structured thumbnail generation template"""
    topic: str
    main_subject: str
    expression_action: str
    composition: str
    background: str
    visual_elements: List[str]
    text_overlay: str
    style: str
    colors: List[str]
    lighting: str
    mood: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "topic": self.topic,
            "main_subject": self.main_subject,
            "expression_action": self.expression_action,
            "composition": self.composition,
            "background": self.background,
            "visual_elements": self.visual_elements,
            "text_overlay": self.text_overlay,
            "style": self.style,
            "colors": self.colors,
            "lighting": self.lighting,
            "mood": self.mood
        }


class ThumbnailTemplateBuilder:
    """Builds structured thumbnail templates from video topics"""
    
    # Topic category mappings
    TOPIC_CATEGORIES = {
        "tech": {
            "subjects": ["laptop", "smartphone", "gadget", "circuit board", "hologram"],
            "expressions": ["amazed", "focused", "excited", "thinking"],
            "compositions": ["split-screen comparison", "product showcase", "hands-on demo"],
            "backgrounds": ["tech workspace", "digital grid", "futuristic lab", "minimalist white"],
            "elements": ["code snippets", "data visualization", "glowing effects", "tech icons"],
            "lighting": "cool blue and cyan",
            "mood": "innovative, cutting-edge"
        },
        "business": {
            "subjects": ["person in business attire", "chart", "growth arrow", "handshake"],
            "expressions": ["confident", "determined", "successful", "professional"],
            "compositions": ["portrait with chart", "upward trend", "team collaboration"],
            "backgrounds": ["office", "financial dashboard", "corporate setting", "gradient"],
            "elements": ["dollar signs", "growth charts", "success badges", "business icons"],
            "lighting": "professional warm and cool",
            "mood": "professional, trustworthy"
        },
        "education": {
            "subjects": ["student", "teacher", "book", "lightbulb", "graduation cap"],
            "expressions": ["curious", "enlightened", "focused", "happy"],
            "compositions": ["learning moment", "knowledge transfer", "achievement"],
            "backgrounds": ["classroom", "library", "digital learning space", "clean white"],
            "elements": ["books", "pencils", "certificates", "knowledge icons"],
            "lighting": "warm and inviting",
            "mood": "educational, inspiring"
        },
        "entertainment": {
            "subjects": ["person with expression", "movie scene", "game character", "music note"],
            "expressions": ["shocked", "laughing", "amazed", "excited"],
            "compositions": ["dramatic moment", "action scene", "emotional peak"],
            "backgrounds": ["movie set", "game world", "stage", "vibrant scene"],
            "elements": ["special effects", "explosions", "stars", "entertainment icons"],
            "lighting": "dramatic and colorful",
            "mood": "exciting, entertaining"
        },
        "lifestyle": {
            "subjects": ["person", "lifestyle item", "nature", "activity"],
            "expressions": ["happy", "relaxed", "inspired", "peaceful"],
            "compositions": ["lifestyle moment", "before-after", "journey"],
            "backgrounds": ["natural setting", "home", "outdoor scene", "lifestyle setting"],
            "elements": ["lifestyle props", "nature elements", "wellness icons", "lifestyle items"],
            "lighting": "natural and warm",
            "mood": "relatable, aspirational"
        },
        "gaming": {
            "subjects": ["game character", "controller", "game scene", "player"],
            "expressions": ["intense", "victorious", "focused", "shocked"],
            "compositions": ["gameplay moment", "character showcase", "epic scene"],
            "backgrounds": ["game world", "gaming setup", "fantasy landscape", "digital world"],
            "elements": ["game UI", "power-ups", "effects", "gaming icons"],
            "lighting": "dynamic and colorful",
            "mood": "intense, thrilling"
        }
    }
    
    # Style-specific prompt modifiers
    STYLE_MODIFIERS = {
        "modern": {
            "composition": "clean, minimalist layout with clear hierarchy",
            "lighting": "bright, even lighting with subtle shadows",
            "mood": "contemporary, sleek, professional",
            "elements": "geometric shapes, flat design, modern typography"
        },
        "bold": {
            "composition": "dramatic, high-contrast composition with focal point",
            "lighting": "dramatic lighting with strong shadows and highlights",
            "mood": "impactful, attention-grabbing, energetic",
            "elements": "bold colors, strong shapes, dramatic effects"
        },
        "minimalist": {
            "composition": "simple, uncluttered layout with maximum white space",
            "lighting": "soft, diffused lighting",
            "mood": "elegant, sophisticated, focused",
            "elements": "minimal elements, clean lines, subtle details"
        },
        "retro": {
            "composition": "vintage-inspired layout with nostalgic elements",
            "lighting": "warm, vintage lighting with film grain",
            "mood": "nostalgic, classic, timeless",
            "elements": "retro colors, vintage typography, classic design"
        }
    }
    
    # Color scheme definitions
    COLOR_SCHEMES = {
        "vibrant": {
            "primary": "#FF6B6B",
            "secondary": "#4ECDC4",
            "accent": "#45B7D1",
            "highlight": "#FFA07A",
            "description": "bright, energetic, eye-catching colors"
        },
        "dark": {
            "primary": "#1A1A1A",
            "secondary": "#2D2D2D",
            "accent": "#404040",
            "highlight": "#555555",
            "description": "dark, professional, sophisticated colors"
        },
        "light": {
            "primary": "#F5F5F5",
            "secondary": "#E8E8E8",
            "accent": "#D0D0D0",
            "highlight": "#B8B8B8",
            "description": "light, clean, minimalist colors"
        },
        "pastel": {
            "primary": "#FFB3BA",
            "secondary": "#FFCCCB",
            "accent": "#FFFFBA",
            "highlight": "#BAE1FF",
            "description": "soft, gentle, pastel colors"
        }
    }
    
    @staticmethod
    def detect_category(topic: str) -> str:
        """Detect topic category from keywords"""
        topic_lower = topic.lower()
        
        # Tech keywords
        if any(word in topic_lower for word in ["ai", "tech", "software", "app", "code", "python", "javascript", "laptop", "phone", "gadget", "robot", "automation"]):
            return "tech"
        
        # Business keywords
        if any(word in topic_lower for word in ["business", "money", "finance", "startup", "entrepreneur", "marketing", "sales", "growth", "investment", "profit"]):
            return "business"
        
        # Education keywords
        if any(word in topic_lower for word in ["learn", "tutorial", "course", "education", "school", "university", "study", "lesson", "guide", "how to"]):
            return "education"
        
        # Entertainment keywords
        if any(word in topic_lower for word in ["movie", "film", "game", "music", "entertainment", "funny", "comedy", "drama", "action", "reaction"]):
            return "entertainment"
        
        # Gaming keywords
        if any(word in topic_lower for word in ["game", "gaming", "esports", "streamer", "gameplay", "console", "pc gaming", "mobile game"]):
            return "gaming"
        
        # Lifestyle keywords
        if any(word in topic_lower for word in ["lifestyle", "fitness", "health", "wellness", "travel", "food", "cooking", "fashion", "beauty", "diy"]):
            return "lifestyle"
        
        # Default to education
        return "education"
    
    @staticmethod
    def build_template(
        topic: str,
        style: str = "modern",
        color_scheme: str = "vibrant"
    ) -> ThumbnailTemplate:
        """Build a structured thumbnail template from a topic"""
        
        # Detect category
        category = ThumbnailTemplateBuilder.detect_category(topic)
        category_data = ThumbnailTemplateBuilder.TOPIC_CATEGORIES.get(category, ThumbnailTemplateBuilder.TOPIC_CATEGORIES["education"])
        
        # Get style modifiers
        style_mod = ThumbnailTemplateBuilder.STYLE_MODIFIERS.get(style, ThumbnailTemplateBuilder.STYLE_MODIFIERS["modern"])
        
        # Get color scheme
        color_data = ThumbnailTemplateBuilder.COLOR_SCHEMES.get(color_scheme, ThumbnailTemplateBuilder.COLOR_SCHEMES["vibrant"])
        colors = [color_data["primary"], color_data["secondary"], color_data["accent"], color_data["highlight"]]
        
        # Build template
        template = ThumbnailTemplate(
            topic=topic,
            main_subject=category_data["subjects"][0],
            expression_action=category_data["expressions"][0],
            composition=style_mod["composition"],
            background=category_data["backgrounds"][0],
            visual_elements=category_data["elements"][:3],
            text_overlay=topic[:30],  # First 30 chars of topic
            style=style,
            colors=colors,
            lighting=style_mod["lighting"],
            mood=style_mod["mood"]
        )
        
        return template
    
    @staticmethod
    def template_to_prompt(template: ThumbnailTemplate) -> str:
        """Convert template to image generation prompt"""
        
        prompt = f"""Generate a YouTube thumbnail image with these specifications:

VISUAL BLUEPRINT:
- Main Subject: {template.main_subject}
- Expression/Action: {template.expression_action}
- Composition: {template.composition}
- Background: {template.background}
- Visual Elements: {', '.join(template.visual_elements)}

DESIGN SPECIFICATIONS:
- Style: {template.style}
- Lighting: {template.lighting}
- Mood: {template.mood}
- Color Palette: {', '.join(template.colors)}

TECHNICAL REQUIREMENTS:
- Resolution: 1280x720 pixels (YouTube standard)
- Format: High contrast, eye-catching design
- Focus: Clear visual hierarchy with strong focal point
- Quality: Professional, polished, viral-worthy

IMPORTANT NOTES:
- Do NOT include text or typography in the image
- Focus only on the visual composition and elements
- Ensure high contrast for thumbnail visibility
- Optimize for small screen viewing
- Create emotional impact through visual design alone

Topic: {template.topic}"""
        
        return prompt
