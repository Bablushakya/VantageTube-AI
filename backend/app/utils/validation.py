"""
Content Validation Module
Validates generated content quality and provides quality scoring
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from collections import Counter


logger = logging.getLogger(__name__)


class ContentValidator:
    """Validates generated content against quality standards"""
    
    # Power words that improve SEO and engagement
    POWER_WORDS = {
        "how", "best", "ultimate", "complete", "guide", "tutorial",
        "tips", "tricks", "secrets", "proven", "essential", "critical",
        "amazing", "incredible", "powerful", "revolutionary", "breakthrough",
        "step-by-step", "easy", "simple", "quick", "fast", "instant",
        "top", "ultimate", "definitive", "comprehensive", "advanced"
    }
    
    # Common keywords that indicate quality titles
    QUALITY_INDICATORS = {
        "2024", "2025", "new", "latest", "updated", "beginner",
        "advanced", "professional", "expert", "master", "learn"
    }
    
    # Minimum and maximum constraints
    TITLE_MIN_LENGTH = 40
    TITLE_MAX_LENGTH = 70
    DESCRIPTION_MIN_WORDS = 200
    DESCRIPTION_MAX_WORDS = 500
    DESCRIPTION_MIN_KEYWORD_DENSITY = 0.01  # 1%
    DESCRIPTION_MAX_KEYWORD_DENSITY = 0.03  # 3%
    TAG_MIN_LENGTH = 2
    TAG_MAX_LENGTH = 50
    THUMBNAIL_TEXT_MIN_WORDS = 2
    THUMBNAIL_TEXT_MAX_WORDS = 6
    
    @staticmethod
    def validate_title(title: str, keywords: Optional[List[str]] = None) -> Tuple[bool, Dict]:
        """
        Validate title meets quality standards
        
        Args:
            title: Title text to validate
            keywords: Optional list of target keywords
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        details = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 100
        }
        
        if not title or not isinstance(title, str):
            details["valid"] = False
            details["errors"].append("Title must be a non-empty string")
            details["score"] = 0
            return False, details
        
        title = title.strip()
        
        # Check length
        if len(title) < ContentValidator.TITLE_MIN_LENGTH:
            details["valid"] = False
            details["errors"].append(
                f"Title too short ({len(title)} chars). Minimum: {ContentValidator.TITLE_MIN_LENGTH}"
            )
            details["score"] -= 30
        elif len(title) > ContentValidator.TITLE_MAX_LENGTH:
            details["valid"] = False
            details["errors"].append(
                f"Title too long ({len(title)} chars). Maximum: {ContentValidator.TITLE_MAX_LENGTH}"
            )
            details["score"] -= 30
        
        # Check for power words
        title_lower = title.lower()
        has_power_word = any(word in title_lower for word in ContentValidator.POWER_WORDS)
        if not has_power_word:
            details["warnings"].append("Title lacks power words (How, Best, Ultimate, etc.)")
            details["score"] -= 10
        
        # Check for keywords
        if keywords:
            has_keyword = any(kw.lower() in title_lower for kw in keywords)
            if not has_keyword:
                details["warnings"].append("Title doesn't contain target keywords")
                details["score"] -= 15
            else:
                details["score"] += 5
        
        # Check for numbers (often improves CTR)
        if re.search(r'\d+', title):
            details["score"] += 5
        
        # Check for question mark (increases engagement)
        if '?' in title:
            details["score"] += 3
        
        # Ensure score is within bounds
        details["score"] = max(0, min(100, details["score"]))
        
        return details["valid"], details
    
    @staticmethod
    def validate_tags(tags: List[str], title: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Validate tags meet quality standards
        
        Args:
            tags: List of tags to validate
            title: Optional title for context
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        details = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 100,
            "tag_count": len(tags),
            "unique_tags": len(set(tags))
        }
        
        if not tags or not isinstance(tags, list):
            details["valid"] = False
            details["errors"].append("Tags must be a non-empty list")
            details["score"] = 0
            return False, details
        
        # Check for duplicates
        if len(set(tags)) < len(tags):
            details["valid"] = False
            details["errors"].append("Tags contain duplicates")
            details["score"] -= 20
        
        # Validate individual tags
        invalid_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                invalid_tags.append(f"Non-string tag: {tag}")
                continue
            
            tag = tag.strip()
            if len(tag) < ContentValidator.TAG_MIN_LENGTH:
                invalid_tags.append(f"Tag too short: '{tag}'")
            elif len(tag) > ContentValidator.TAG_MAX_LENGTH:
                invalid_tags.append(f"Tag too long: '{tag}'")
        
        if invalid_tags:
            details["valid"] = False
            details["errors"].extend(invalid_tags[:5])  # Limit to 5 errors
            details["score"] -= 25
        
        # Check tag count
        if len(tags) < 5:
            details["warnings"].append(f"Low tag count ({len(tags)}). Recommended: 15-30")
            details["score"] -= 10
        elif len(tags) > 30:
            details["warnings"].append(f"High tag count ({len(tags)}). Recommended: 15-30")
            details["score"] -= 5
        
        # Check for relevance to title
        if title:
            title_words = set(title.lower().split())
            tag_words = set(' '.join(tags).lower().split())
            overlap = len(title_words & tag_words)
            if overlap == 0:
                details["warnings"].append("Tags don't overlap with title keywords")
                details["score"] -= 10
        
        # Ensure score is within bounds
        details["score"] = max(0, min(100, details["score"]))
        
        return details["valid"], details
    
    @staticmethod
    def validate_description(
        description: str,
        keywords: Optional[List[str]] = None
    ) -> Tuple[bool, Dict]:
        """
        Validate description meets quality standards
        
        Args:
            description: Description text to validate
            keywords: Optional list of target keywords
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        details = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 100,
            "word_count": 0,
            "keyword_density": 0.0,
            "has_structure": False
        }
        
        if not description or not isinstance(description, str):
            details["valid"] = False
            details["errors"].append("Description must be a non-empty string")
            details["score"] = 0
            return False, details
        
        description = description.strip()
        
        # Count words
        words = description.split()
        word_count = len(words)
        details["word_count"] = word_count
        
        # Check word count
        if word_count < ContentValidator.DESCRIPTION_MIN_WORDS:
            details["valid"] = False
            details["errors"].append(
                f"Description too short ({word_count} words). Minimum: {ContentValidator.DESCRIPTION_MIN_WORDS}"
            )
            details["score"] -= 40
        elif word_count > ContentValidator.DESCRIPTION_MAX_WORDS:
            details["valid"] = False
            details["errors"].append(
                f"Description too long ({word_count} words). Maximum: {ContentValidator.DESCRIPTION_MAX_WORDS}"
            )
            details["score"] -= 20
        
        # Check for structure (paragraphs/sections)
        paragraphs = [p.strip() for p in description.split('\n') if p.strip()]
        if len(paragraphs) >= 2:
            details["has_structure"] = True
            details["score"] += 5
        else:
            details["warnings"].append("Description lacks clear structure/paragraphs")
            details["score"] -= 10
        
        # Check keyword density
        if keywords:
            keyword_count = 0
            description_lower = description.lower()
            for keyword in keywords:
                keyword_lower = keyword.lower()
                keyword_count += description_lower.count(keyword_lower)
            
            keyword_density = keyword_count / word_count if word_count > 0 else 0
            details["keyword_density"] = round(keyword_density, 4)
            
            if keyword_density < ContentValidator.DESCRIPTION_MIN_KEYWORD_DENSITY:
                details["warnings"].append(
                    f"Low keyword density ({keyword_density:.2%}). Target: 1-3%"
                )
                details["score"] -= 15
            elif keyword_density > ContentValidator.DESCRIPTION_MAX_KEYWORD_DENSITY:
                details["valid"] = False
                details["errors"].append(
                    f"Keyword density too high ({keyword_density:.2%}). Maximum: 3%"
                )
                details["score"] -= 30
            else:
                details["score"] += 10
        
        # Check for CTA
        cta_keywords = ["subscribe", "like", "comment", "click", "visit", "check out"]
        has_cta = any(cta in description.lower() for cta in cta_keywords)
        if has_cta:
            details["score"] += 5
        else:
            details["warnings"].append("Description lacks call-to-action")
            details["score"] -= 5
        
        # Ensure score is within bounds
        details["score"] = max(0, min(100, details["score"]))
        
        return details["valid"], details
    
    @staticmethod
    def validate_thumbnail_text(text: str) -> Tuple[bool, Dict]:
        """
        Validate thumbnail text meets quality standards
        
        Args:
            text: Thumbnail text to validate
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        details = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 100,
            "word_count": 0
        }
        
        if not text or not isinstance(text, str):
            details["valid"] = False
            details["errors"].append("Thumbnail text must be a non-empty string")
            details["score"] = 0
            return False, details
        
        text = text.strip()
        
        # Count words
        words = text.split()
        word_count = len(words)
        details["word_count"] = word_count
        
        # Check word count
        if word_count < ContentValidator.THUMBNAIL_TEXT_MIN_WORDS:
            details["valid"] = False
            details["errors"].append(
                f"Thumbnail text too short ({word_count} words). Minimum: {ContentValidator.THUMBNAIL_TEXT_MIN_WORDS}"
            )
            details["score"] -= 40
        elif word_count > ContentValidator.THUMBNAIL_TEXT_MAX_WORDS:
            details["valid"] = False
            details["errors"].append(
                f"Thumbnail text too long ({word_count} words). Maximum: {ContentValidator.THUMBNAIL_TEXT_MAX_WORDS}"
            )
            details["score"] -= 40
        
        # Check for readability (no special characters that might be hard to read)
        special_char_count = len(re.findall(r'[^a-zA-Z0-9\s\?\!\-]', text))
        if special_char_count > 2:
            details["warnings"].append("Thumbnail text contains many special characters")
            details["score"] -= 10
        
        # Check for uppercase (good for thumbnails)
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if uppercase_ratio > 0.5:
            details["score"] += 5
        
        # Ensure score is within bounds
        details["score"] = max(0, min(100, details["score"]))
        
        return details["valid"], details


class QualityScorer:
    """Calculates quality scores for generated content"""
    
    @staticmethod
    def calculate_title_quality_score(
        title: str,
        keywords: Optional[List[str]] = None
    ) -> float:
        """Calculate quality score for a title (0-100)"""
        _, details = ContentValidator.validate_title(title, keywords)
        return details["score"]
    
    @staticmethod
    def calculate_tags_quality_score(
        tags: List[str],
        title: Optional[str] = None
    ) -> float:
        """Calculate quality score for tags (0-100)"""
        _, details = ContentValidator.validate_tags(tags, title)
        return details["score"]
    
    @staticmethod
    def calculate_description_quality_score(
        description: str,
        keywords: Optional[List[str]] = None
    ) -> float:
        """Calculate quality score for description (0-100)"""
        _, details = ContentValidator.validate_description(description, keywords)
        return details["score"]
    
    @staticmethod
    def calculate_thumbnail_quality_score(text: str) -> float:
        """Calculate quality score for thumbnail text (0-100)"""
        _, details = ContentValidator.validate_thumbnail_text(text)
        return details["score"]
    
    @staticmethod
    def calculate_batch_quality_score(
        titles: List[Dict],
        tags: Dict,
        description: Dict,
        thumbnail_texts: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate quality scores for batch generation
        
        Args:
            titles: List of title dicts with 'text' key
            tags: Tags dict with 'tags' key
            description: Description dict with 'description' key
            thumbnail_texts: List of thumbnail text dicts with 'text' key
            
        Returns:
            Dict with quality scores for each content type
        """
        scores = {}
        
        # Calculate title scores
        if titles:
            title_scores = [
                QualityScorer.calculate_title_quality_score(t.get('text', ''))
                for t in titles
            ]
            scores['titles'] = round(sum(title_scores) / len(title_scores), 2) if title_scores else 0
        
        # Calculate tags score
        if tags and 'tags' in tags:
            scores['tags'] = QualityScorer.calculate_tags_quality_score(tags['tags'])
        
        # Calculate description score
        if description and 'description' in description:
            scores['description'] = QualityScorer.calculate_description_quality_score(
                description['description']
            )
        
        # Calculate thumbnail scores
        if thumbnail_texts:
            thumbnail_scores = [
                QualityScorer.calculate_thumbnail_quality_score(t.get('text', ''))
                for t in thumbnail_texts
            ]
            scores['thumbnail_text'] = round(sum(thumbnail_scores) / len(thumbnail_scores), 2) if thumbnail_scores else 0
        
        return scores


class RegenerationLogic:
    """Handles regeneration of failed content"""
    
    @staticmethod
    def should_regenerate(validation_details: Dict) -> bool:
        """
        Determine if content should be regenerated
        
        Args:
            validation_details: Validation details dict
            
        Returns:
            True if content should be regenerated
        """
        # Regenerate if validation failed or score is too low
        return not validation_details.get("valid", False) or validation_details.get("score", 0) < 60
    
    @staticmethod
    def get_regeneration_hints(validation_details: Dict) -> List[str]:
        """
        Get hints for regeneration based on validation failures
        
        Args:
            validation_details: Validation details dict
            
        Returns:
            List of hints for improving content
        """
        hints = []
        
        # Add error-based hints
        for error in validation_details.get("errors", []):
            if "too short" in error.lower():
                hints.append("Expand content to meet minimum length requirements")
            elif "too long" in error.lower():
                hints.append("Reduce content to meet maximum length requirements")
            elif "duplicate" in error.lower():
                hints.append("Remove duplicate tags")
            elif "keyword density" in error.lower():
                hints.append("Adjust keyword usage to meet 1-3% density target")
        
        # Add warning-based hints
        for warning in validation_details.get("warnings", []):
            if "power word" in warning.lower():
                hints.append("Include power words like 'How', 'Best', 'Ultimate'")
            elif "keyword" in warning.lower():
                hints.append("Incorporate target keywords more prominently")
            elif "structure" in warning.lower():
                hints.append("Add clear structure with paragraphs or sections")
            elif "call-to-action" in warning.lower():
                hints.append("Include a clear call-to-action")
        
        return hints


# Create singleton instances
validator = ContentValidator()
scorer = QualityScorer()
regeneration_logic = RegenerationLogic()
