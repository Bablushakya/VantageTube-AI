"""
VantageTube AI - SEO Analysis Service
Handles video SEO scoring and analysis
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
from app.core.supabase import get_supabase
from app.models.seo import (
    SEOCriterion,
    SEOSuggestion,
    VideoAnalysisResponse
)
from fastapi import HTTPException, status


class SEOAnalyzer:
    """SEO Analysis Engine"""
    
    # Weights for each criterion (must sum to 1.0)
    WEIGHTS = {
        'title': 0.25,
        'description': 0.20,
        'tags': 0.15,
        'thumbnail': 0.15,
        'engagement': 0.25
    }
    
    # Common high-performing keywords
    POWER_WORDS = [
        'how to', 'tutorial', 'guide', 'tips', 'tricks', 'best', 'top',
        'review', 'vs', 'comparison', 'ultimate', 'complete', 'beginner',
        'advanced', 'pro', 'easy', 'simple', 'quick', 'fast', 'new',
        '2024', '2025', 'free', 'secret', 'hack', 'amazing', 'incredible'
    ]
    
    @staticmethod
    def analyze_title(title: str, tags: List[str] = None) -> Tuple[int, SEOCriterion]:
        """
        Analyze video title
        
        Scoring criteria:
        - Length (40-70 characters is optimal)
        - Contains keywords/power words
        - Not all caps
        - Contains numbers (performs better)
        - Keyword placement (front-loaded is better)
        """
        score = 0
        details = []
        
        # Length check (30 points)
        length = len(title)
        if 40 <= length <= 70:
            score += 30
            details.append("✓ Optimal length (40-70 chars)")
        elif 30 <= length < 40 or 70 < length <= 80:
            score += 20
            details.append("⚠ Length could be optimized (40-70 chars is best)")
        elif length < 30:
            score += 10
            details.append("✗ Title too short (aim for 40-70 chars)")
        else:
            score += 15
            details.append("✗ Title too long (aim for 40-70 chars)")
        
        # Power words check (25 points)
        title_lower = title.lower()
        power_words_found = [word for word in SEOAnalyzer.POWER_WORDS if word in title_lower]
        if len(power_words_found) >= 2:
            score += 25
            details.append(f"✓ Contains power words: {', '.join(power_words_found[:3])}")
        elif len(power_words_found) == 1:
            score += 15
            details.append(f"⚠ Contains power word: {power_words_found[0]}")
        else:
            score += 5
            details.append("✗ No power words found (e.g., 'how to', 'best', 'guide')")
        
        # Capitalization check (15 points)
        if title.isupper():
            score += 0
            details.append("✗ Avoid ALL CAPS titles")
        elif title[0].isupper():
            score += 15
            details.append("✓ Proper capitalization")
        else:
            score += 10
            details.append("⚠ Consider capitalizing first letter")
        
        # Numbers check (15 points)
        if re.search(r'\d+', title):
            score += 15
            details.append("✓ Contains numbers (increases CTR)")
        else:
            score += 5
            details.append("⚠ Consider adding numbers (e.g., '5 Tips', '2024')")
        
        # Keyword placement (15 points)
        if tags and len(tags) > 0:
            # Check if main keywords appear in first half of title
            first_half = title_lower[:len(title)//2]
            keywords_in_front = any(tag.lower() in first_half for tag in tags[:3])
            if keywords_in_front:
                score += 15
                details.append("✓ Keywords front-loaded")
            else:
                score += 8
                details.append("⚠ Move keywords to beginning of title")
        else:
            score += 10
        
        # Determine status
        if score >= 80:
            status = 'excellent'
            message = "Excellent title optimization!"
        elif score >= 60:
            status = 'good'
            message = "Good title, minor improvements possible"
        elif score >= 40:
            status = 'fair'
            message = "Title needs optimization"
        else:
            status = 'poor'
            message = "Title requires significant improvement"
        
        criterion = SEOCriterion(
            name="Title Optimization",
            score=score,
            weight=SEOAnalyzer.WEIGHTS['title'],
            status=status,
            message=message,
            details="\n".join(details)
        )
        
        return score, criterion
    
    @staticmethod
    def analyze_description(description: str) -> Tuple[int, SEOCriterion]:
        """
        Analyze video description
        
        Scoring criteria:
        - Length (200+ characters is good)
        - Contains links
        - Contains timestamps
        - Contains keywords
        - Has call-to-action
        """
        score = 0
        details = []
        
        if not description:
            return 0, SEOCriterion(
                name="Description Optimization",
                score=0,
                weight=SEOAnalyzer.WEIGHTS['description'],
                status='poor',
                message="No description provided",
                details="Add a detailed description to improve SEO"
            )
        
        length = len(description)
        
        # Length check (30 points)
        if length >= 500:
            score += 30
            details.append("✓ Comprehensive description (500+ chars)")
        elif length >= 200:
            score += 20
            details.append("⚠ Good length, consider adding more detail")
        elif length >= 100:
            score += 10
            details.append("✗ Description too short (aim for 200+ chars)")
        else:
            score += 5
            details.append("✗ Very short description (aim for 200+ chars)")
        
        # Links check (20 points)
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', description)
        if len(links) >= 3:
            score += 20
            details.append(f"✓ Contains {len(links)} links")
        elif len(links) >= 1:
            score += 15
            details.append(f"⚠ Contains {len(links)} link(s), add more resources")
        else:
            score += 5
            details.append("✗ No links found (add social media, website, resources)")
        
        # Timestamps check (20 points)
        timestamps = re.findall(r'\d{1,2}:\d{2}', description)
        if len(timestamps) >= 3:
            score += 20
            details.append(f"✓ Contains {len(timestamps)} timestamps")
        elif len(timestamps) >= 1:
            score += 10
            details.append(f"⚠ Contains {len(timestamps)} timestamp(s), add more chapters")
        else:
            score += 0
            details.append("✗ No timestamps (add chapter markers)")
        
        # Keywords check (15 points)
        desc_lower = description.lower()
        keywords_found = [word for word in SEOAnalyzer.POWER_WORDS if word in desc_lower]
        if len(keywords_found) >= 3:
            score += 15
            details.append("✓ Good keyword density")
        elif len(keywords_found) >= 1:
            score += 10
            details.append("⚠ Add more relevant keywords")
        else:
            score += 5
            details.append("✗ Low keyword density")
        
        # Call-to-action check (15 points)
        cta_words = ['subscribe', 'like', 'comment', 'share', 'follow', 'click', 'watch', 'check out']
        has_cta = any(word in desc_lower for word in cta_words)
        if has_cta:
            score += 15
            details.append("✓ Contains call-to-action")
        else:
            score += 5
            details.append("✗ Add call-to-action (subscribe, like, comment)")
        
        # Determine status
        if score >= 80:
            status = 'excellent'
            message = "Excellent description!"
        elif score >= 60:
            status = 'good'
            message = "Good description, minor improvements possible"
        elif score >= 40:
            status = 'fair'
            message = "Description needs optimization"
        else:
            status = 'poor'
            message = "Description requires improvement"
        
        criterion = SEOCriterion(
            name="Description Optimization",
            score=score,
            weight=SEOAnalyzer.WEIGHTS['description'],
            status=status,
            message=message,
            details="\n".join(details)
        )
        
        return score, criterion
    
    @staticmethod
    def analyze_tags(tags: List[str], title: str, description: str) -> Tuple[int, SEOCriterion]:
        """
        Analyze video tags
        
        Scoring criteria:
        - Number of tags (10-15 is optimal)
        - Tag relevance to title/description
        - Mix of broad and specific tags
        - Tag length variety
        """
        score = 0
        details = []
        
        if not tags or len(tags) == 0:
            return 0, SEOCriterion(
                name="Tags Optimization",
                score=0,
                weight=SEOAnalyzer.WEIGHTS['tags'],
                status='poor',
                message="No tags provided",
                details="Add 10-15 relevant tags to improve discoverability"
            )
        
        tag_count = len(tags)
        
        # Count check (30 points)
        if 10 <= tag_count <= 15:
            score += 30
            details.append(f"✓ Optimal tag count ({tag_count} tags)")
        elif 5 <= tag_count < 10 or 15 < tag_count <= 20:
            score += 20
            details.append(f"⚠ {tag_count} tags (aim for 10-15)")
        elif tag_count < 5:
            score += 10
            details.append(f"✗ Too few tags ({tag_count}), add more")
        else:
            score += 15
            details.append(f"⚠ Too many tags ({tag_count}), focus on quality")
        
        # Relevance check (30 points)
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        relevant_tags = [tag for tag in tags if tag.lower() in title_lower or tag.lower() in desc_lower]
        relevance_ratio = len(relevant_tags) / len(tags) if tags else 0
        
        if relevance_ratio >= 0.7:
            score += 30
            details.append(f"✓ High relevance ({len(relevant_tags)}/{len(tags)} tags match content)")
        elif relevance_ratio >= 0.4:
            score += 20
            details.append(f"⚠ Moderate relevance ({len(relevant_tags)}/{len(tags)} tags match)")
        else:
            score += 10
            details.append(f"✗ Low relevance ({len(relevant_tags)}/{len(tags)} tags match)")
        
        # Tag variety check (20 points)
        short_tags = [tag for tag in tags if len(tag.split()) == 1]
        long_tags = [tag for tag in tags if len(tag.split()) >= 2]
        
        if len(short_tags) > 0 and len(long_tags) > 0:
            score += 20
            details.append(f"✓ Good mix of broad ({len(short_tags)}) and specific ({len(long_tags)}) tags")
        else:
            score += 10
            details.append("⚠ Add mix of single-word and multi-word tags")
        
        # Duplicate check (20 points)
        unique_tags = len(set(tag.lower() for tag in tags))
        if unique_tags == len(tags):
            score += 20
            details.append("✓ No duplicate tags")
        else:
            score += 10
            details.append(f"⚠ {len(tags) - unique_tags} duplicate tag(s) found")
        
        # Determine status
        if score >= 80:
            status = 'excellent'
            message = "Excellent tag optimization!"
        elif score >= 60:
            status = 'good'
            message = "Good tags, minor improvements possible"
        elif score >= 40:
            status = 'fair'
            message = "Tags need optimization"
        else:
            status = 'poor'
            message = "Tags require improvement"
        
        criterion = SEOCriterion(
            name="Tags Optimization",
            score=score,
            weight=SEOAnalyzer.WEIGHTS['tags'],
            status=status,
            message=message,
            details="\n".join(details)
        )
        
        return score, criterion
    
    @staticmethod
    def analyze_thumbnail(thumbnail_url: str, title: str) -> Tuple[int, SEOCriterion]:
        """
        Analyze thumbnail (basic analysis without image processing)
        
        Note: Full thumbnail analysis would require image processing
        For now, we check if thumbnail exists and provide general guidelines
        """
        score = 0
        details = []
        
        if not thumbnail_url:
            return 0, SEOCriterion(
                name="Thumbnail Optimization",
                score=0,
                weight=SEOAnalyzer.WEIGHTS['thumbnail'],
                status='poor',
                message="No custom thumbnail",
                details="Upload a custom thumbnail to improve CTR"
            )
        
        # Has custom thumbnail (50 points)
        score += 50
        details.append("✓ Custom thumbnail uploaded")
        
        # General best practices (50 points distributed)
        details.append("⚠ Thumbnail best practices:")
        details.append("  • Use 1280x720 resolution (16:9 ratio)")
        details.append("  • Add text overlay (3-5 words max)")
        details.append("  • Use high contrast colors")
        details.append("  • Include faces (increases CTR by 30%)")
        details.append("  • Avoid clickbait")
        details.append("  • Match video content")
        score += 30  # Assume decent thumbnail if custom
        
        # Determine status
        if score >= 80:
            status = 'excellent'
            message = "Good thumbnail setup"
        elif score >= 60:
            status = 'good'
            message = "Thumbnail present, follow best practices"
        else:
            status = 'fair'
            message = "Thumbnail needs optimization"
        
        criterion = SEOCriterion(
            name="Thumbnail Optimization",
            score=score,
            weight=SEOAnalyzer.WEIGHTS['thumbnail'],
            status=status,
            message=message,
            details="\n".join(details)
        )
        
        return score, criterion
    
    @staticmethod
    def analyze_engagement(views: int, likes: int, comments: int, duration: int) -> Tuple[int, SEOCriterion]:
        """
        Analyze engagement metrics
        
        Scoring criteria:
        - Like-to-view ratio
        - Comment-to-view ratio
        - Engagement rate
        """
        score = 0
        details = []
        
        if views == 0:
            return 50, SEOCriterion(
                name="Engagement Metrics",
                score=50,
                weight=SEOAnalyzer.WEIGHTS['engagement'],
                status='fair',
                message="New video, no engagement data yet",
                details="Promote video to get initial engagement"
            )
        
        # Like-to-view ratio (40 points)
        like_ratio = (likes / views) * 100 if views > 0 else 0
        if like_ratio >= 5:
            score += 40
            details.append(f"✓ Excellent like ratio ({like_ratio:.2f}%)")
        elif like_ratio >= 3:
            score += 30
            details.append(f"✓ Good like ratio ({like_ratio:.2f}%)")
        elif like_ratio >= 1:
            score += 20
            details.append(f"⚠ Fair like ratio ({like_ratio:.2f}%)")
        else:
            score += 10
            details.append(f"✗ Low like ratio ({like_ratio:.2f}%)")
        
        # Comment-to-view ratio (30 points)
        comment_ratio = (comments / views) * 100 if views > 0 else 0
        if comment_ratio >= 0.5:
            score += 30
            details.append(f"✓ Excellent comment ratio ({comment_ratio:.2f}%)")
        elif comment_ratio >= 0.2:
            score += 20
            details.append(f"✓ Good comment ratio ({comment_ratio:.2f}%)")
        elif comment_ratio >= 0.1:
            score += 15
            details.append(f"⚠ Fair comment ratio ({comment_ratio:.2f}%)")
        else:
            score += 5
            details.append(f"✗ Low comment ratio ({comment_ratio:.2f}%)")
        
        # Overall engagement (30 points)
        engagement_score = likes + (comments * 2)  # Comments weighted more
        engagement_rate = (engagement_score / views) * 100 if views > 0 else 0
        
        if engagement_rate >= 5:
            score += 30
            details.append(f"✓ High engagement rate ({engagement_rate:.2f}%)")
        elif engagement_rate >= 3:
            score += 20
            details.append(f"✓ Good engagement rate ({engagement_rate:.2f}%)")
        elif engagement_rate >= 1:
            score += 15
            details.append(f"⚠ Moderate engagement rate ({engagement_rate:.2f}%)")
        else:
            score += 10
            details.append(f"✗ Low engagement rate ({engagement_rate:.2f}%)")
        
        # Determine status
        if score >= 80:
            status = 'excellent'
            message = "Excellent engagement!"
        elif score >= 60:
            status = 'good'
            message = "Good engagement metrics"
        elif score >= 40:
            status = 'fair'
            message = "Engagement could be improved"
        else:
            status = 'poor'
            message = "Low engagement, needs improvement"
        
        criterion = SEOCriterion(
            name="Engagement Metrics",
            score=score,
            weight=SEOAnalyzer.WEIGHTS['engagement'],
            status=status,
            message=message,
            details="\n".join(details)
        )
        
        return score, criterion
    
    @staticmethod
    def generate_suggestions(criteria: List[SEOCriterion], video_data: Dict[str, Any]) -> List[SEOSuggestion]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        for criterion in criteria:
            if criterion.score < 60:  # Only suggest improvements for low scores
                if criterion.name == "Title Optimization":
                    suggestions.append(SEOSuggestion(
                        type="title",
                        priority="high",
                        title="Optimize Your Title",
                        description="Aim for 40-70 characters, include power words like 'how to', 'best', or 'guide', and front-load keywords.",
                        impact="Can increase CTR by 20-30%"
                    ))
                
                elif criterion.name == "Description Optimization":
                    suggestions.append(SEOSuggestion(
                        type="description",
                        priority="high",
                        title="Enhance Your Description",
                        description="Write at least 200 characters, add timestamps, include 3+ links, and add a call-to-action.",
                        impact="Improves SEO ranking and viewer retention"
                    ))
                
                elif criterion.name == "Tags Optimization":
                    suggestions.append(SEOSuggestion(
                        type="tags",
                        priority="medium",
                        title="Improve Your Tags",
                        description="Use 10-15 relevant tags, mix broad and specific keywords, ensure tags match your content.",
                        impact="Increases discoverability by 15-25%"
                    ))
                
                elif criterion.name == "Thumbnail Optimization":
                    suggestions.append(SEOSuggestion(
                        type="thumbnail",
                        priority="high",
                        title="Create Better Thumbnail",
                        description="Use 1280x720 resolution, add text overlay (3-5 words), use high contrast, include faces if possible.",
                        impact="Can increase CTR by 30-50%"
                    ))
                
                elif criterion.name == "Engagement Metrics":
                    suggestions.append(SEOSuggestion(
                        type="engagement",
                        priority="medium",
                        title="Boost Engagement",
                        description="Ask questions in video, encourage likes/comments, respond to comments, create community posts.",
                        impact="Improves algorithm ranking"
                    ))
        
        # Always add general suggestions
        if len(suggestions) == 0:
            suggestions.append(SEOSuggestion(
                type="general",
                priority="low",
                title="Maintain Your Performance",
                description="Your video is well-optimized! Continue monitoring analytics and engaging with your audience.",
                impact="Sustained growth"
            ))
        
        return suggestions
    
    @staticmethod
    def calculate_overall_score(criteria: List[SEOCriterion]) -> int:
        """Calculate weighted overall score"""
        total_score = sum(criterion.score * criterion.weight for criterion in criteria)
        return int(total_score)
    
    @staticmethod
    def get_grade(score: int) -> str:
        """Get letter grade from score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"


class SEOService:
    """Service for SEO analysis operations"""
    
    @staticmethod
    async def analyze_video(video_db_id: str, user_id: str, force_reanalysis: bool = False) -> VideoAnalysisResponse:
        """
        Analyze video SEO
        
        Args:
            video_db_id: Video database ID
            user_id: User ID
            force_reanalysis: Force re-analysis even if recent analysis exists
            
        Returns:
            Video analysis response with scores and suggestions
        """
        supabase = get_supabase()
        
        try:
            # Get video from database
            video_response = supabase.table("videos").select("*").eq("id", video_db_id).eq("user_id", user_id).execute()
            
            if not video_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
            
            video_data = video_response.data[0]
            
            # Check if recent analysis exists (within last 24 hours)
            if not force_reanalysis and video_data.get("last_analyzed_at"):
                last_analyzed = datetime.fromisoformat(video_data["last_analyzed_at"])
                hours_since = (datetime.utcnow() - last_analyzed).total_seconds() / 3600
                
                if hours_since < 24:
                    # Return existing analysis
                    report_response = supabase.table("seo_reports").select("*").eq("video_id", video_db_id).order("created_at", desc=True).limit(1).execute()
                    
                    if report_response.data:
                        report = report_response.data[0]
                        return VideoAnalysisResponse(
                            video_id=video_db_id,
                            video_title=video_data["title"],
                            overall_score=report["overall_score"],
                            grade=SEOAnalyzer.get_grade(report["overall_score"]),
                            criteria=[SEOCriterion(**c) for c in report["criteria_breakdown"]],
                            suggestions=[SEOSuggestion(**s) for s in report["suggestions"]],
                            analyzed_at=datetime.fromisoformat(report["created_at"])
                        )
            
            # Perform analysis
            title_score, title_criterion = SEOAnalyzer.analyze_title(
                video_data["title"],
                video_data.get("tags", [])
            )
            
            desc_score, desc_criterion = SEOAnalyzer.analyze_description(
                video_data.get("description", "")
            )
            
            tags_score, tags_criterion = SEOAnalyzer.analyze_tags(
                video_data.get("tags", []),
                video_data["title"],
                video_data.get("description", "")
            )
            
            thumb_score, thumb_criterion = SEOAnalyzer.analyze_thumbnail(
                video_data.get("thumbnail_url", ""),
                video_data["title"]
            )
            
            engagement_score, engagement_criterion = SEOAnalyzer.analyze_engagement(
                video_data.get("view_count", 0),
                video_data.get("like_count", 0),
                video_data.get("comment_count", 0),
                video_data.get("duration", 0)
            )
            
            criteria = [
                title_criterion,
                desc_criterion,
                tags_criterion,
                thumb_criterion,
                engagement_criterion
            ]
            
            # Calculate overall score
            overall_score = SEOAnalyzer.calculate_overall_score(criteria)
            
            # Generate suggestions
            suggestions = SEOAnalyzer.generate_suggestions(criteria, video_data)
            
            # Save report to database
            report_data = {
                "user_id": user_id,
                "video_id": video_db_id,
                "overall_score": overall_score,
                "title_score": title_score,
                "description_score": desc_score,
                "tags_score": tags_score,
                "thumbnail_score": thumb_score,
                "engagement_score": engagement_score,
                "suggestions": [s.model_dump() for s in suggestions],
                "criteria_breakdown": [c.model_dump() for c in criteria]
            }
            
            supabase.table("seo_reports").insert(report_data).execute()
            
            # Update video with SEO score and last_analyzed_at
            supabase.table("videos").update({
                "seo_score": overall_score,
                "last_analyzed_at": datetime.utcnow().isoformat()
            }).eq("id", video_db_id).execute()
            
            return VideoAnalysisResponse(
                video_id=video_db_id,
                video_title=video_data["title"],
                overall_score=overall_score,
                grade=SEOAnalyzer.get_grade(overall_score),
                criteria=criteria,
                suggestions=suggestions,
                analyzed_at=datetime.utcnow()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze video: {str(e)}"
            )
    
    @staticmethod
    async def get_video_reports(video_db_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all SEO reports for a video"""
        supabase = get_supabase()
        
        try:
            response = supabase.table("seo_reports").select("*").eq("video_id", video_db_id).eq("user_id", user_id).order("created_at", desc=True).execute()
            
            return response.data
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get reports: {str(e)}"
            )
