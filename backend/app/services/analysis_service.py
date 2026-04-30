"""
Content Analysis Service
Analyzes trending videos and extracts content patterns
"""

from typing import List, Dict, Optional, Tuple
from collections import Counter
import re
from datetime import datetime
from app.models.trending import TrendingVideoResponse
from app.models.generator import ContentPattern


class AnalysisService:
    """Service for analyzing trending videos and extracting patterns"""
    
    def __init__(self):
        """Initialize analysis service"""
        self.stop_words = {
            'with', 'from', 'this', 'that', 'have', 'will', 'your', 'more', 'about',
            'what', 'when', 'where', 'which', 'their', 'there', 'the', 'a', 'an',
            'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are',
            'be', 'been', 'being', 'has', 'had', 'do', 'does', 'did', 'can', 'could',
            'should', 'would', 'may', 'might', 'must', 'shall', 'by', 'as', 'if'
        }
    
    async def extract_content_patterns(
        self,
        videos: List[TrendingVideoResponse]
    ) -> Dict[str, ContentPattern]:
        """
        Extract content patterns from trending videos
        
        Args:
            videos: List of trending videos to analyze
            
        Returns:
            Dictionary of content patterns with keywords as keys
        """
        if not videos:
            return {}
        
        patterns = {}
        
        # Extract keywords from titles
        title_keywords = self._extract_keywords_from_texts(
            [v.title for v in videos]
        )
        
        # Extract keywords from descriptions
        desc_keywords = self._extract_keywords_from_texts(
            [v.description or "" for v in videos]
        )
        
        # Extract tags
        all_tags = []
        for video in videos:
            all_tags.extend(video.tags)
        
        # Combine all keywords
        all_keywords = title_keywords + desc_keywords + all_tags
        keyword_counts = Counter(all_keywords)
        
        # Calculate metrics for each keyword
        for keyword, count in keyword_counts.most_common(50):
            # Find videos containing this keyword
            matching_videos = [
                v for v in videos
                if keyword.lower() in (v.title + " " + (v.description or "")).lower()
                or keyword in v.tags
            ]
            
            if matching_videos:
                avg_viral_score = sum(v.viral_score for v in matching_videos) / len(matching_videos)
                avg_engagement_rate = sum(v.engagement_rate for v in matching_videos) / len(matching_videos)
                
                patterns[keyword] = ContentPattern(
                    keyword=keyword,
                    frequency=count,
                    avg_viral_score=round(avg_viral_score, 2),
                    avg_engagement_rate=round(avg_engagement_rate, 2)
                )
        
        return patterns
    
    async def identify_title_patterns(
        self,
        videos: List[TrendingVideoResponse]
    ) -> List[str]:
        """
        Identify common title structures and patterns
        
        Args:
            videos: List of trending videos
            
        Returns:
            List of common title patterns
        """
        if not videos:
            return []
        
        patterns = []
        pattern_counts = Counter()
        
        for video in videos:
            title = video.title
            
            # Check for common patterns
            if title.lower().startswith("how to"):
                pattern_counts["How to [action]"] += 1
            elif title.lower().startswith("complete guide"):
                pattern_counts["Complete Guide to [topic]"] += 1
            elif title.lower().startswith("ultimate"):
                pattern_counts["Ultimate [topic] Guide"] += 1
            elif title.lower().startswith("best"):
                pattern_counts["Best [topic] for [audience]"] += 1
            elif "tutorial" in title.lower():
                pattern_counts["[Topic] Tutorial for [audience]"] += 1
            elif ":" in title:
                pattern_counts["[Main]: [Subtitle]"] += 1
            elif "vs" in title.lower() or "versus" in title.lower():
                pattern_counts["[Option A] vs [Option B]"] += 1
            elif any(year in title for year in ["2024", "2023", "2022"]):
                pattern_counts["[Topic] [Year]"] += 1
            elif "[" in title and "]" in title:
                pattern_counts["[Bracketed] Content"] += 1
            else:
                pattern_counts["Direct Statement"] += 1
        
        # Return top patterns
        for pattern, count in pattern_counts.most_common(10):
            patterns.append(pattern)
        
        return patterns
    
    async def calculate_niche_relevance(
        self,
        video: TrendingVideoResponse,
        niche: str
    ) -> float:
        """
        Calculate how relevant a video is to a specific niche
        
        Args:
            video: Video to evaluate
            niche: Niche to match against
            
        Returns:
            Relevance score (0-100)
        """
        niche_lower = niche.lower()
        niche_words = set(re.findall(r'\w+', niche_lower))
        
        # Combine title, description, and tags
        content = f"{video.title} {video.description or ''} {' '.join(video.tags)}".lower()
        content_words = set(re.findall(r'\w+', content))
        
        # Calculate word overlap
        matches = len(niche_words.intersection(content_words))
        match_ratio = matches / len(niche_words) if niche_words else 0
        
        # Calculate semantic similarity (simple approach)
        # Check for related terms
        related_matches = 0
        for niche_word in niche_words:
            if niche_word in content:
                related_matches += 1
        
        relevance_score = (match_ratio * 100 + (related_matches / len(niche_words) * 50 if niche_words else 0)) / 2
        
        return round(min(relevance_score, 100), 2)
    
    async def identify_opportunities(
        self,
        videos: List[TrendingVideoResponse],
        patterns: Dict[str, ContentPattern]
    ) -> List[str]:
        """
        Identify content opportunities based on trending analysis
        
        Args:
            videos: Trending videos
            patterns: Extracted content patterns
            
        Returns:
            List of opportunity insights
        """
        opportunities = []
        
        if not videos:
            return opportunities
        
        # Analyze engagement patterns
        avg_engagement = sum(v.engagement_rate for v in videos) / len(videos)
        high_engagement_videos = [v for v in videos if v.engagement_rate > avg_engagement * 1.5]
        
        if high_engagement_videos:
            # Extract keywords from high-engagement videos
            high_eng_keywords = []
            for v in high_engagement_videos:
                high_eng_keywords.extend(self._extract_keywords_from_texts([v.title]))
            
            top_keywords = Counter(high_eng_keywords).most_common(3)
            if top_keywords:
                keywords_str = ", ".join([k[0] for k in top_keywords])
                opportunities.append(f"High engagement on content about: {keywords_str}")
        
        # Analyze viral score distribution
        viral_scores = [v.viral_score for v in videos]
        avg_viral = sum(viral_scores) / len(viral_scores)
        high_viral_videos = [v for v in videos if v.viral_score > avg_viral * 1.3]
        
        if high_viral_videos:
            opportunities.append(f"Strong viral potential: {len(high_viral_videos)} videos trending with high viral scores")
        
        # Analyze recency
        recent_videos = [v for v in videos if (datetime.utcnow() - v.published_at.replace(tzinfo=None)).days < 7]
        if recent_videos:
            opportunities.append(f"Recent trend: {len(recent_videos)} videos published in last 7 days")
        
        # Analyze top keywords
        if patterns:
            top_patterns = sorted(patterns.values(), key=lambda x: x.frequency, reverse=True)[:5]
            top_keywords = [p.keyword for p in top_patterns]
            opportunities.append(f"Top trending keywords: {', '.join(top_keywords)}")
        
        # Analyze title patterns
        title_patterns = await self.identify_title_patterns(videos)
        if title_patterns:
            opportunities.append(f"Effective title patterns: {', '.join(title_patterns[:3])}")
        
        # Analyze engagement vs views ratio
        high_engagement_ratio = [v for v in videos if v.engagement_rate > 5]
        if high_engagement_ratio:
            opportunities.append(f"High engagement content: {len(high_engagement_ratio)} videos with >5% engagement rate")
        
        return opportunities
    
    def _extract_keywords_from_texts(self, texts: List[str]) -> List[str]:
        """
        Extract keywords from a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of extracted keywords
        """
        keywords = []
        
        for text in texts:
            if not text:
                continue
            
            # Extract words (4+ characters)
            words = re.findall(r'\b\w{4,}\b', text.lower())
            
            # Filter out stop words
            filtered_words = [w for w in words if w not in self.stop_words]
            
            keywords.extend(filtered_words)
        
        return keywords
    
    async def analyze_tag_patterns(
        self,
        videos: List[TrendingVideoResponse]
    ) -> Dict[str, int]:
        """
        Analyze tag usage patterns
        
        Args:
            videos: List of trending videos
            
        Returns:
            Dictionary of tag frequencies
        """
        all_tags = []
        
        for video in videos:
            all_tags.extend(video.tags)
        
        tag_counts = Counter(all_tags)
        
        return dict(tag_counts.most_common(30))
    
    async def calculate_content_opportunity_score(
        self,
        video: TrendingVideoResponse,
        niche_relevance: float
    ) -> float:
        """
        Calculate overall content opportunity score
        
        Args:
            video: Video to score
            niche_relevance: Niche relevance score (0-100)
            
        Returns:
            Opportunity score (0-100)
        """
        # Factors: viral score, engagement, recency, niche relevance
        
        # Viral score component (40%)
        viral_component = video.viral_score * 0.4
        
        # Engagement component (30%)
        engagement_component = min(video.engagement_rate * 10, 100) * 0.3
        
        # Recency component (20%)
        hours_old = (datetime.utcnow() - video.published_at.replace(tzinfo=None)).total_seconds() / 3600
        if hours_old < 24:
            recency_component = 100 * 0.2
        elif hours_old < 72:
            recency_component = 50 * 0.2
        else:
            recency_component = 25 * 0.2
        
        # Niche relevance component (10%)
        niche_component = niche_relevance * 0.1
        
        opportunity_score = viral_component + engagement_component + recency_component + niche_component
        
        return round(min(opportunity_score, 100), 2)
    
    async def identify_trending_topics(
        self,
        videos: List[TrendingVideoResponse],
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Identify trending topics from video titles
        
        Args:
            videos: List of trending videos
            limit: Maximum topics to return
            
        Returns:
            List of (topic, frequency) tuples
        """
        all_keywords = []
        
        for video in videos:
            keywords = self._extract_keywords_from_texts([video.title])
            all_keywords.extend(keywords)
        
        keyword_counts = Counter(all_keywords)
        
        return keyword_counts.most_common(limit)


# Create singleton instance
analysis_service = AnalysisService()

