"""
Trending Topics Service
Handles YouTube trending videos fetching and analysis
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from app.core.config import settings
from app.core.supabase import get_supabase
from app.models.trending import (
    TrendingVideoResponse, TrendingVideoCreate,
    ViralScoreBreakdown, TrendingAnalysis,
    TrendingStatsResponse, ContentOpportunity,
    YOUTUBE_CATEGORIES
)
import re
from collections import Counter


class TrendingService:
    """Service for trending videos analysis"""
    
    def __init__(self):
        """Initialize YouTube API client (lazy-loaded)"""
        self._youtube = None
    
    @property
    def youtube(self):
        """Lazy-load YouTube API client"""
        if self._youtube is None:
            if not settings.YOUTUBE_API_KEY or settings.YOUTUBE_API_KEY == "your_youtube_api_key":
                raise ValueError("YOUTUBE_API_KEY not configured. Please set a valid YouTube API key in .env")
            self._youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        return self._youtube
    
    async def fetch_trending_videos(
        self,
        region: str = "US",
        category_id: Optional[str] = None,
        max_results: int = 50
    ) -> List[TrendingVideoResponse]:
        """
        Fetch trending videos from YouTube
        
        Args:
            region: Region code (US, GB, IN, etc.)
            category_id: YouTube category ID (optional)
            max_results: Maximum results (1-50)
            
        Returns:
            List of trending videos with viral scores
        """
        try:
            # Build request parameters
            request_params = {
                'part': 'snippet,statistics,contentDetails',
                'chart': 'mostPopular',
                'regionCode': region,
                'maxResults': max_results
            }
            
            if category_id:
                request_params['videoCategoryId'] = category_id
            
            # Fetch from YouTube API
            request = self.youtube.videos().list(**request_params)
            response = request.execute()
            
            # Process videos
            trending_videos = []
            for idx, item in enumerate(response.get('items', [])):
                video_data = self._parse_video_data(item, idx + 1, region)
                if video_data:
                    trending_videos.append(video_data)
            
            # Save to database
            await self._save_trending_videos(trending_videos)
            
            return trending_videos
            
        except Exception as e:
            raise Exception(f"Failed to fetch trending videos: {str(e)}")
    
    def _parse_video_data(
        self,
        item: dict,
        rank: int,
        region: str
    ) -> Optional[TrendingVideoCreate]:
        """Parse YouTube API response item into TrendingVideoCreate"""
        try:
            snippet = item['snippet']
            statistics = item['statistics']
            
            # Extract data
            youtube_video_id = item['id']
            title = snippet['title']
            channel_title = snippet['channelTitle']
            channel_id = snippet['channelId']
            description = snippet.get('description', '')
            thumbnail_url = snippet['thumbnails']['high']['url']
            published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
            
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            category_id = snippet.get('categoryId', '0')
            tags = snippet.get('tags', [])
            
            # Calculate viral score
            viral_score = self._calculate_viral_score(
                view_count, like_count, comment_count, published_at
            )
            
            # Calculate engagement rate
            engagement_rate = self._calculate_engagement_rate(
                view_count, like_count, comment_count
            )
            
            return TrendingVideoCreate(
                youtube_video_id=youtube_video_id,
                title=title,
                channel_title=channel_title,
                channel_id=channel_id,
                description=description,
                thumbnail_url=thumbnail_url,
                published_at=published_at,
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                category_id=category_id,
                tags=tags,
                viral_score=viral_score,
                engagement_rate=engagement_rate,
                trending_rank=rank,
                region=region
            )
            
        except Exception as e:
            print(f"Error parsing video data: {str(e)}")
            return None
    
    def _calculate_viral_score(
        self,
        views: int,
        likes: int,
        comments: int,
        published_at: datetime
    ) -> float:
        """
        Calculate viral score (0-100) based on multiple factors
        
        Factors:
        - View velocity (views per hour)
        - Engagement rate
        - Recency bonus
        """
        # Calculate hours since publish
        hours_since_publish = max((datetime.utcnow() - published_at.replace(tzinfo=None)).total_seconds() / 3600, 1)
        
        # View velocity (views per hour)
        view_velocity = views / hours_since_publish
        
        # Normalize view velocity (log scale)
        # 1000 views/hour = 50 points, 10000 views/hour = 75 points, 100000+ = 100 points
        if view_velocity < 10:
            velocity_score = view_velocity * 2  # 0-20
        elif view_velocity < 100:
            velocity_score = 20 + (view_velocity - 10) * 0.33  # 20-50
        elif view_velocity < 1000:
            velocity_score = 50 + (view_velocity - 100) * 0.028  # 50-75
        else:
            velocity_score = min(75 + (view_velocity - 1000) * 0.00025, 100)  # 75-100
        
        # Engagement rate score
        if views > 0:
            engagement_rate = ((likes + comments) / views) * 100
            # Good engagement: 5%+ = 100 points, 2-5% = 50-100, <2% = 0-50
            if engagement_rate >= 5:
                engagement_score = 100
            elif engagement_rate >= 2:
                engagement_score = 50 + ((engagement_rate - 2) / 3) * 50
            else:
                engagement_score = (engagement_rate / 2) * 50
        else:
            engagement_score = 0
        
        # Recency bonus (newer videos get bonus)
        if hours_since_publish < 24:
            recency_bonus = 20 * (1 - hours_since_publish / 24)  # 0-20 points
        elif hours_since_publish < 72:
            recency_bonus = 10 * (1 - (hours_since_publish - 24) / 48)  # 0-10 points
        else:
            recency_bonus = 0
        
        # Weighted score
        viral_score = (
            velocity_score * 0.5 +      # 50% weight
            engagement_score * 0.35 +   # 35% weight
            recency_bonus * 0.15        # 15% weight
        )
        
        return min(round(viral_score, 2), 100)
    
    def _calculate_engagement_rate(
        self,
        views: int,
        likes: int,
        comments: int
    ) -> float:
        """Calculate engagement rate as percentage"""
        if views == 0:
            return 0.0
        return round(((likes + comments) / views) * 100, 2)
    
    async def _save_trending_videos(
        self,
        videos: List[TrendingVideoCreate]
    ) -> None:
        """Save trending videos to database"""
        supabase = get_supabase()
        
        try:
            # Prepare data for insertion
            videos_data = [
                {
                    "youtube_video_id": video.youtube_video_id,
                    "title": video.title,
                    "channel_title": video.channel_title,
                    "channel_id": video.channel_id,
                    "description": video.description,
                    "thumbnail_url": video.thumbnail_url,
                    "published_at": video.published_at.isoformat(),
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "comment_count": video.comment_count,
                    "category_id": video.category_id,
                    "tags": video.tags,
                    "viral_score": video.viral_score,
                    "engagement_rate": video.engagement_rate,
                    "trending_rank": video.trending_rank,
                    "region": video.region,
                    "fetched_at": datetime.utcnow().isoformat()
                }
                for video in videos
            ]
            
            # Insert into database (upsert to avoid duplicates)
            supabase.table("trending_topics").upsert(
                videos_data,
                on_conflict="youtube_video_id,region"
            ).execute()
            
        except Exception as e:
            print(f"Error saving trending videos: {str(e)}")
    
    async def get_trending_videos(
        self,
        keywords: Optional[List[str]] = None,
        min_views: Optional[int] = None,
        min_viral_score: Optional[float] = None,
        category_id: Optional[str] = None,
        region: str = "US",
        limit: int = 20
    ) -> List[TrendingVideoResponse]:
        """
        Get trending videos from database with filters
        
        Args:
            keywords: Filter by keywords in title/description
            min_views: Minimum view count
            min_viral_score: Minimum viral score
            category_id: Filter by category
            region: Region code
            limit: Maximum results
            
        Returns:
            List of filtered trending videos
        """
        supabase = get_supabase()
        
        try:
            # Build query
            query = supabase.table("trending_topics").select("*").eq("region", region)
            
            if category_id:
                query = query.eq("category_id", category_id)
            
            if min_views:
                query = query.gte("view_count", min_views)
            
            if min_viral_score:
                query = query.gte("viral_score", min_viral_score)
            
            # Execute query
            result = query.order("viral_score", desc=True).limit(limit).execute()
            
            videos = []
            for item in result.data:
                # Filter by keywords if provided
                if keywords:
                    title_desc = f"{item['title']} {item.get('description', '')}".lower()
                    if not any(keyword.lower() in title_desc for keyword in keywords):
                        continue
                
                videos.append(TrendingVideoResponse(
                    id=item['id'],
                    youtube_video_id=item['youtube_video_id'],
                    title=item['title'],
                    channel_title=item['channel_title'],
                    channel_id=item['channel_id'],
                    description=item.get('description'),
                    thumbnail_url=item.get('thumbnail_url'),
                    published_at=datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')),
                    view_count=item['view_count'],
                    like_count=item['like_count'],
                    comment_count=item['comment_count'],
                    category_id=item['category_id'],
                    tags=item.get('tags', []),
                    viral_score=item['viral_score'],
                    engagement_rate=item['engagement_rate'],
                    trending_rank=item['trending_rank'],
                    region=item['region'],
                    fetched_at=datetime.fromisoformat(item['fetched_at'].replace('Z', '+00:00'))
                ))
            
            return videos[:limit]
            
        except Exception as e:
            raise Exception(f"Failed to get trending videos: {str(e)}")
    
    async def analyze_trending_video(
        self,
        video_id: str,
        user_niche: Optional[str] = None
    ) -> TrendingAnalysis:
        """
        Analyze a trending video in detail
        
        Args:
            video_id: Trending video database ID
            user_niche: User's content niche for match scoring
            
        Returns:
            Detailed analysis of the trending video
        """
        supabase = get_supabase()
        
        try:
            # Get video from database
            result = supabase.table("trending_topics").select("*").eq("id", video_id).execute()
            
            if not result.data:
                raise Exception("Trending video not found")
            
            item = result.data[0]
            
            # Create video response
            video = TrendingVideoResponse(
                id=item['id'],
                youtube_video_id=item['youtube_video_id'],
                title=item['title'],
                channel_title=item['channel_title'],
                channel_id=item['channel_id'],
                description=item.get('description'),
                thumbnail_url=item.get('thumbnail_url'),
                published_at=datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')),
                view_count=item['view_count'],
                like_count=item['like_count'],
                comment_count=item['comment_count'],
                category_id=item['category_id'],
                tags=item.get('tags', []),
                viral_score=item['viral_score'],
                engagement_rate=item['engagement_rate'],
                trending_rank=item['trending_rank'],
                region=item['region'],
                fetched_at=datetime.fromisoformat(item['fetched_at'].replace('Z', '+00:00'))
            )
            
            # Calculate viral score breakdown
            hours_since_publish = (datetime.utcnow() - video.published_at.replace(tzinfo=None)).total_seconds() / 3600
            view_velocity = video.view_count / max(hours_since_publish, 1)
            
            breakdown = ViralScoreBreakdown(
                view_velocity=round(view_velocity, 2),
                engagement_rate=video.engagement_rate,
                like_ratio=round((video.like_count / video.view_count * 100) if video.view_count > 0 else 0, 2),
                comment_ratio=round((video.comment_count / video.view_count * 100) if video.view_count > 0 else 0, 2),
                recency_bonus=20 if hours_since_publish < 24 else (10 if hours_since_publish < 72 else 0),
                total_score=video.viral_score
            )
            
            # Calculate niche match if provided
            niche_match = None
            if user_niche:
                niche_match = self._calculate_niche_match(video, user_niche)
            
            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(video)
            
            # Generate insights
            insights = self._generate_insights(video, breakdown)
            
            return TrendingAnalysis(
                video=video,
                viral_score_breakdown=breakdown,
                niche_match=niche_match,
                opportunity_score=opportunity_score,
                insights=insights
            )
            
        except Exception as e:
            raise Exception(f"Failed to analyze trending video: {str(e)}")
    
    def _calculate_niche_match(self, video: TrendingVideoResponse, user_niche: str) -> float:
        """Calculate how well video matches user's niche (0-100)"""
        niche_lower = user_niche.lower()
        title_desc = f"{video.title} {video.description or ''}".lower()
        tags_str = " ".join(video.tags).lower()
        
        # Check for keyword matches
        niche_words = set(niche_lower.split())
        content_words = set(re.findall(r'\w+', title_desc + " " + tags_str))
        
        matches = len(niche_words.intersection(content_words))
        match_ratio = matches / len(niche_words) if niche_words else 0
        
        return round(match_ratio * 100, 2)
    
    def _calculate_opportunity_score(self, video: TrendingVideoResponse) -> float:
        """Calculate content opportunity score (0-100)"""
        # Factors: viral score, engagement, recency, competition (inverse of views)
        
        # High viral score = good opportunity
        viral_component = video.viral_score * 0.4
        
        # High engagement = good opportunity
        engagement_component = min(video.engagement_rate * 10, 100) * 0.3
        
        # Recent videos = better opportunity
        hours_old = (datetime.utcnow() - video.published_at.replace(tzinfo=None)).total_seconds() / 3600
        recency_component = (100 if hours_old < 24 else (50 if hours_old < 72 else 25)) * 0.2
        
        # Lower views = less competition (easier to compete)
        if video.view_count < 100000:
            competition_component = 100
        elif video.view_count < 500000:
            competition_component = 75
        elif video.view_count < 1000000:
            competition_component = 50
        else:
            competition_component = 25
        competition_component *= 0.1
        
        opportunity_score = viral_component + engagement_component + recency_component + competition_component
        
        return round(min(opportunity_score, 100), 2)
    
    def _generate_insights(self, video: TrendingVideoResponse, breakdown: ViralScoreBreakdown) -> List[str]:
        """Generate insights about the trending video"""
        insights = []
        
        # View velocity insight
        if breakdown.view_velocity > 10000:
            insights.append(f"🔥 Extremely high view velocity: {breakdown.view_velocity:.0f} views/hour")
        elif breakdown.view_velocity > 1000:
            insights.append(f"📈 Strong view velocity: {breakdown.view_velocity:.0f} views/hour")
        
        # Engagement insight
        if breakdown.engagement_rate > 5:
            insights.append(f"💬 Exceptional engagement rate: {breakdown.engagement_rate}%")
        elif breakdown.engagement_rate > 2:
            insights.append(f"👍 Good engagement rate: {breakdown.engagement_rate}%")
        
        # Recency insight
        if breakdown.recency_bonus > 0:
            insights.append("⏰ Recently trending - act fast to capitalize on this trend")
        
        # Category insight
        category_name = YOUTUBE_CATEGORIES.get(video.category_id, "Unknown")
        insights.append(f"📂 Category: {category_name}")
        
        # Tags insight
        if len(video.tags) > 0:
            insights.append(f"🏷️ Uses {len(video.tags)} tags - consider similar tagging strategy")
        
        return insights
    
    async def get_trending_stats(self, region: str = "US") -> TrendingStatsResponse:
        """Get statistics about trending videos"""
        supabase = get_supabase()
        
        try:
            # Get all trending videos for region
            result = supabase.table("trending_topics").select("*").eq("region", region).execute()
            
            videos = result.data
            
            if not videos:
                return TrendingStatsResponse(
                    total_videos=0,
                    average_views=0,
                    average_viral_score=0,
                    top_categories=[],
                    trending_keywords=[],
                    last_fetch=None
                )
            
            # Calculate statistics
            total_videos = len(videos)
            average_views = sum(v['view_count'] for v in videos) // total_videos
            average_viral_score = round(sum(v['viral_score'] for v in videos) / total_videos, 2)
            
            # Top categories
            category_counts = Counter(v['category_id'] for v in videos)
            top_categories = [
                {"category_id": cat_id, "category_name": YOUTUBE_CATEGORIES.get(cat_id, "Unknown"), "count": count}
                for cat_id, count in category_counts.most_common(5)
            ]
            
            # Trending keywords (from titles)
            all_words = []
            for v in videos:
                words = re.findall(r'\b\w{4,}\b', v['title'].lower())
                all_words.extend(words)
            
            # Filter common words
            stop_words = {'with', 'from', 'this', 'that', 'have', 'will', 'your', 'more', 'about', 'what', 'when', 'where', 'which', 'their', 'there'}
            filtered_words = [w for w in all_words if w not in stop_words]
            
            word_counts = Counter(filtered_words)
            trending_keywords = [
                {"keyword": word, "count": count}
                for word, count in word_counts.most_common(10)
            ]
            
            # Last fetch time
            last_fetch = max(datetime.fromisoformat(v['fetched_at'].replace('Z', '+00:00')) for v in videos)
            
            return TrendingStatsResponse(
                total_videos=total_videos,
                average_views=average_views,
                average_viral_score=average_viral_score,
                top_categories=top_categories,
                trending_keywords=trending_keywords,
                last_fetch=last_fetch
            )
            
        except Exception as e:
            raise Exception(f"Failed to get trending stats: {str(e)}")
    
    async def identify_content_opportunities(
        self,
        user_niche: str,
        region: str = "US",
        limit: int = 5
    ) -> List[ContentOpportunity]:
        """
        Identify content opportunities based on trending videos
        
        Args:
            user_niche: User's content niche
            region: Region code
            limit: Maximum opportunities to return
            
        Returns:
            List of content opportunities
        """
        # Get trending videos
        videos = await self.get_trending_videos(region=region, limit=50)
        
        # Filter by niche relevance
        relevant_videos = []
        for video in videos:
            niche_match = self._calculate_niche_match(video, user_niche)
            if niche_match > 30:  # At least 30% match
                relevant_videos.append((video, niche_match))
        
        # Group by topic clusters
        # This is a simplified version - could use NLP for better clustering
        opportunities = []
        
        # For now, return top opportunities based on viral score and niche match
        relevant_videos.sort(key=lambda x: (x[0].viral_score + x[1]) / 2, reverse=True)
        
        for video, niche_match in relevant_videos[:limit]:
            # Extract keywords from title
            keywords = re.findall(r'\b\w{4,}\b', video.title.lower())
            keywords = [k for k in keywords if k not in {'with', 'from', 'this', 'that'}][:5]
            
            # Determine competition level
            if video.view_count < 100000:
                competition = "Low"
            elif video.view_count < 500000:
                competition = "Medium"
            else:
                competition = "High"
            
            opportunity = ContentOpportunity(
                topic=video.title,
                keyword_cluster=keywords,
                trending_videos_count=1,
                average_views=video.view_count,
                competition_level=competition,
                opportunity_score=self._calculate_opportunity_score(video),
                recommended_approach=f"Create similar content targeting: {', '.join(keywords[:3])}",
                sample_titles=[video.title]
            )
            
            opportunities.append(opportunity)
        
        return opportunities


# Create singleton instance
trending_service = TrendingService()
