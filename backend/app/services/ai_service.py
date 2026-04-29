"""
AI Content Generation Service
Handles OpenAI API integration for content generation
"""

import openai
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.models.content import (
    GeneratedTitle, GeneratedTitles, GeneratedDescription,
    GeneratedTags, ThumbnailTextSuggestion, GeneratedThumbnailText
)


class AIService:
    """Service for AI-powered content generation using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured in environment variables")
        openai.api_key = settings.OPENAI_API_KEY
    
    async def generate_titles(
        self,
        topic: str,
        keywords: List[str],
        tone: str = "professional",
        target_audience: Optional[str] = None,
        count: int = 5
    ) -> GeneratedTitles:
        """
        Generate optimized video titles using AI
        
        Args:
            topic: Video topic/subject
            keywords: Target keywords for SEO
            tone: Content tone (professional, casual, enthusiastic, educational)
            target_audience: Target audience description
            count: Number of titles to generate
            
        Returns:
            GeneratedTitles with multiple title options
        """
        # Build prompt
        prompt = self._build_title_prompt(topic, keywords, tone, target_audience, count)
        
        try:
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube SEO specialist who creates high-performing video titles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            titles = self._parse_titles_response(content)
            
            return GeneratedTitles(
                titles=titles,
                topic=topic,
                keywords=keywords,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise Exception(f"Failed to generate titles: {str(e)}")
    
    async def generate_description(
        self,
        topic: str,
        title: Optional[str] = None,
        keywords: List[str] = None,
        tone: str = "professional",
        target_audience: Optional[str] = None,
        video_length: Optional[str] = None,
        include_timestamps: bool = True,
        include_links: bool = True,
        include_cta: bool = True
    ) -> GeneratedDescription:
        """
        Generate optimized video description using AI
        
        Args:
            topic: Video topic/subject
            title: Video title for context
            keywords: Target keywords for SEO
            tone: Content tone
            target_audience: Target audience description
            video_length: Video length (short, medium, long)
            include_timestamps: Include timestamp placeholders
            include_links: Include link placeholders
            include_cta: Include call-to-action
            
        Returns:
            GeneratedDescription with optimized description
        """
        # Build prompt
        prompt = self._build_description_prompt(
            topic, title, keywords, tone, target_audience, video_length,
            include_timestamps, include_links, include_cta
        )
        
        try:
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube SEO specialist who creates engaging, SEO-optimized video descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse response
            content = response.choices[0].message.content
            description_data = self._parse_description_response(content)
            
            return GeneratedDescription(
                description=description_data["description"],
                word_count=len(description_data["description"].split()),
                includes_timestamps=include_timestamps and "[00:00]" in description_data["description"],
                includes_links=include_links and "http" in description_data["description"],
                includes_cta=include_cta,
                seo_tips=description_data.get("seo_tips", []),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise Exception(f"Failed to generate description: {str(e)}")
    
    async def generate_tags(
        self,
        topic: str,
        title: Optional[str] = None,
        keywords: List[str] = None,
        count: int = 15
    ) -> GeneratedTags:
        """
        Generate optimized video tags using AI
        
        Args:
            topic: Video topic/subject
            title: Video title for context
            keywords: Target keywords
            count: Number of tags to generate
            
        Returns:
            GeneratedTags with categorized tags
        """
        # Build prompt
        prompt = self._build_tags_prompt(topic, title, keywords, count)
        
        try:
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube SEO specialist who creates effective video tags for maximum discoverability."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=800
            )
            
            # Parse response
            content = response.choices[0].message.content
            tags_data = self._parse_tags_response(content)
            
            return GeneratedTags(
                tags=tags_data["tags"],
                tag_count=len(tags_data["tags"]),
                tag_categories=tags_data["categories"],
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise Exception(f"Failed to generate tags: {str(e)}")
    
    async def generate_thumbnail_text(
        self,
        topic: str,
        title: Optional[str] = None,
        count: int = 5
    ) -> GeneratedThumbnailText:
        """
        Generate thumbnail text suggestions using AI
        
        Args:
            topic: Video topic/subject
            title: Video title for context
            count: Number of suggestions
            
        Returns:
            GeneratedThumbnailText with text suggestions and design tips
        """
        # Build prompt
        prompt = self._build_thumbnail_prompt(topic, title, count)
        
        try:
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube thumbnail designer who creates compelling thumbnail text that drives clicks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            thumbnail_data = self._parse_thumbnail_response(content)
            
            return GeneratedThumbnailText(
                suggestions=thumbnail_data["suggestions"],
                design_tips=thumbnail_data["design_tips"],
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise Exception(f"Failed to generate thumbnail text: {str(e)}")
    
    # ==================== Prompt Builders ====================
    
    def _build_title_prompt(
        self,
        topic: str,
        keywords: List[str],
        tone: str,
        target_audience: Optional[str],
        count: int
    ) -> str:
        """Build prompt for title generation"""
        keywords_str = ", ".join(keywords) if keywords else "N/A"
        audience_str = f" targeting {target_audience}" if target_audience else ""
        
        return f"""Generate {count} highly optimized YouTube video titles for the following:

Topic: {topic}
Keywords: {keywords_str}
Tone: {tone}
Target Audience: {target_audience or "General"}{audience_str}

Requirements:
- Length: 40-70 characters (optimal for YouTube)
- Include power words (How to, Best, Ultimate, Complete, Guide, etc.)
- Include numbers when relevant
- Front-load important keywords
- Use proper capitalization
- Make it click-worthy but not clickbait
- Each title should be unique and compelling

For each title, provide:
1. The title text
2. SEO score estimate (0-100)
3. Brief reasoning why it works

Format your response as:
TITLE 1: [title text]
SCORE: [0-100]
REASONING: [why it works]

TITLE 2: [title text]
SCORE: [0-100]
REASONING: [why it works]

... and so on."""
    
    def _build_description_prompt(
        self,
        topic: str,
        title: Optional[str],
        keywords: List[str],
        tone: str,
        target_audience: Optional[str],
        video_length: Optional[str],
        include_timestamps: bool,
        include_links: bool,
        include_cta: bool
    ) -> str:
        """Build prompt for description generation"""
        keywords_str = ", ".join(keywords) if keywords else "N/A"
        title_str = f"\nTitle: {title}" if title else ""
        
        return f"""Generate an optimized YouTube video description for:

Topic: {topic}{title_str}
Keywords: {keywords_str}
Tone: {tone}
Target Audience: {target_audience or "General"}
Video Length: {video_length or "Medium"}

Requirements:
- Length: 200-300 words minimum
- First 2-3 sentences are crucial (appear above "Show More")
- Include keywords naturally (don't stuff)
- {"Include timestamp placeholders (e.g., 00:00 Intro, 02:15 Main Topic)" if include_timestamps else "No timestamps needed"}
- {"Include 3-5 relevant link placeholders (resources, social media, etc.)" if include_links else "No links needed"}
- {"Include a strong call-to-action (subscribe, like, comment)" if include_cta else "No CTA needed"}
- Use line breaks for readability
- Add relevant hashtags at the end (3-5 hashtags)

Also provide 3-5 SEO tips specific to this description.

Format your response as:
DESCRIPTION:
[description text here]

SEO_TIPS:
- [tip 1]
- [tip 2]
- [tip 3]"""
    
    def _build_tags_prompt(
        self,
        topic: str,
        title: Optional[str],
        keywords: List[str],
        count: int
    ) -> str:
        """Build prompt for tags generation"""
        keywords_str = ", ".join(keywords) if keywords else "N/A"
        title_str = f"\nTitle: {title}" if title else ""
        
        return f"""Generate {count} optimized YouTube video tags for:

Topic: {topic}{title_str}
Keywords: {keywords_str}

Requirements:
- Mix of broad and specific tags
- Include exact keywords from title
- Include related/synonym keywords
- Include long-tail keywords (2-3 word phrases)
- No duplicate tags
- Relevant to the video content
- Help with discoverability

Categorize tags into:
1. Primary (exact topic/keywords)
2. Secondary (related topics)
3. Long-tail (specific phrases)
4. Broad (general category)

Format your response as:
PRIMARY:
- [tag 1]
- [tag 2]

SECONDARY:
- [tag 3]
- [tag 4]

LONG_TAIL:
- [tag 5]
- [tag 6]

BROAD:
- [tag 7]
- [tag 8]"""
    
    def _build_thumbnail_prompt(
        self,
        topic: str,
        title: Optional[str],
        count: int
    ) -> str:
        """Build prompt for thumbnail text generation"""
        title_str = f"\nTitle: {title}" if title else ""
        
        return f"""Generate {count} compelling thumbnail text suggestions for:

Topic: {topic}{title_str}

Requirements:
- Short and punchy (2-6 words max)
- Large, readable text
- Creates curiosity or urgency
- Complements the title (doesn't repeat it exactly)
- Various styles: bold statement, question, number, minimal

For each suggestion, provide:
1. The text
2. Suggested style (bold, minimal, question, number)
3. Brief reasoning

Also provide 5 general thumbnail design tips.

Format your response as:
SUGGESTION 1:
TEXT: [text]
STYLE: [style]
REASONING: [why it works]

SUGGESTION 2:
TEXT: [text]
STYLE: [style]
REASONING: [why it works]

... and so on.

DESIGN_TIPS:
- [tip 1]
- [tip 2]
- [tip 3]
- [tip 4]
- [tip 5]"""
    
    # ==================== Response Parsers ====================
    
    def _parse_titles_response(self, content: str) -> List[GeneratedTitle]:
        """Parse AI response for titles"""
        titles = []
        lines = content.strip().split("\n")
        
        current_title = {}
        for line in lines:
            line = line.strip()
            if line.startswith("TITLE"):
                if current_title:
                    titles.append(GeneratedTitle(**current_title))
                current_title = {"text": line.split(":", 1)[1].strip()}
            elif line.startswith("SCORE"):
                try:
                    current_title["score"] = int(line.split(":", 1)[1].strip())
                except:
                    current_title["score"] = 75
            elif line.startswith("REASONING"):
                current_title["reasoning"] = line.split(":", 1)[1].strip()
        
        if current_title:
            titles.append(GeneratedTitle(**current_title))
        
        return titles
    
    def _parse_description_response(self, content: str) -> Dict:
        """Parse AI response for description"""
        parts = content.split("SEO_TIPS:")
        description = parts[0].replace("DESCRIPTION:", "").strip()
        
        seo_tips = []
        if len(parts) > 1:
            tips_text = parts[1].strip()
            seo_tips = [
                line.strip("- ").strip()
                for line in tips_text.split("\n")
                if line.strip().startswith("-")
            ]
        
        return {
            "description": description,
            "seo_tips": seo_tips
        }
    
    def _parse_tags_response(self, content: str) -> Dict:
        """Parse AI response for tags"""
        tags = []
        categories = {
            "primary": [],
            "secondary": [],
            "long_tail": [],
            "broad": []
        }
        
        current_category = None
        lines = content.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("PRIMARY:"):
                current_category = "primary"
            elif line.startswith("SECONDARY:"):
                current_category = "secondary"
            elif line.startswith("LONG_TAIL:"):
                current_category = "long_tail"
            elif line.startswith("BROAD:"):
                current_category = "broad"
            elif line.startswith("-") and current_category:
                tag = line.strip("- ").strip()
                if tag:
                    tags.append(tag)
                    categories[current_category].append(tag)
        
        return {
            "tags": tags,
            "categories": categories
        }
    
    def _parse_thumbnail_response(self, content: str) -> Dict:
        """Parse AI response for thumbnail text"""
        suggestions = []
        design_tips = []
        
        parts = content.split("DESIGN_TIPS:")
        suggestions_text = parts[0]
        
        # Parse suggestions
        lines = suggestions_text.strip().split("\n")
        current_suggestion = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("SUGGESTION"):
                if current_suggestion:
                    suggestions.append(ThumbnailTextSuggestion(**current_suggestion))
                current_suggestion = {}
            elif line.startswith("TEXT:"):
                current_suggestion["text"] = line.split(":", 1)[1].strip()
            elif line.startswith("STYLE:"):
                current_suggestion["style"] = line.split(":", 1)[1].strip()
            elif line.startswith("REASONING:"):
                current_suggestion["reasoning"] = line.split(":", 1)[1].strip()
        
        if current_suggestion:
            suggestions.append(ThumbnailTextSuggestion(**current_suggestion))
        
        # Parse design tips
        if len(parts) > 1:
            tips_text = parts[1].strip()
            design_tips = [
                line.strip("- ").strip()
                for line in tips_text.split("\n")
                if line.strip().startswith("-")
            ]
        
        return {
            "suggestions": suggestions,
            "design_tips": design_tips
        }


# Create singleton instance
ai_service = AIService()
