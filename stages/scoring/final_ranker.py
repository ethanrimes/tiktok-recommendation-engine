"""Final ranking stage."""

from typing import List, Dict, Any
from config import settings

class FinalRanker:
    """Combine scores and rank videos."""
    
    def rank(
        self,
        videos: List[Dict[str, Any]],
        virality_scores: Dict[str, float],
        relevance_scores: Dict[str, float],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank videos based on combined scores.
        
        Args:
            videos: List of video dictionaries
            virality_scores: Video ID to virality score mapping
            relevance_scores: Video ID to relevance score mapping
            user_profile: User profile with tags
            
        Returns:
            List of ranked recommendations
        """
        recommendations = []
        
        for video in videos:
            video_id = video.get('id')
            if not video_id:
                continue
            
            # Get individual scores
            virality = virality_scores.get(video_id, 0.5)
            relevance = relevance_scores.get(video_id, 0.5)
            
            # Calculate engagement quality score
            engagement = self._calculate_engagement_quality(video)
            
            # Apply weights from config
            final_score = (
                virality * settings.virality_weight +
                relevance * settings.relevance_weight +
                engagement * settings.engagement_weight
            )
            
            # Find matched tags
            matched_tags = self._find_matched_tags(video, user_profile.get('tags', []))
            
            # Create recommendation object
            recommendation = {
                'video_id': video_id,
                'description': video.get('description', ''),
                'author': video.get('author', ''),
                'url': video.get('url', ''),
                'score': final_score,
                'scores': {
                    'virality': virality,
                    'relevance': relevance,
                    'engagement': engagement
                },
                'matched_tags': matched_tags,
                'stats': video.get('stats', {}),
                'create_time': video.get('create_time'),
                'music_title': video.get('music_title', ''),
                'hashtags': video.get('hashtags', [])
            }
            
            recommendations.append(recommendation)
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversity boost to prevent monotony
        recommendations = self._apply_diversity_boost(recommendations)
        
        return recommendations
    
    def _calculate_engagement_quality(self, video: Dict[str, Any]) -> float:
        """Calculate engagement quality score."""
        stats = video.get('stats', {})
        
        plays = stats.get('plays', 0)
        likes = stats.get('likes', 0)
        comments = stats.get('comments', 0)
        shares = stats.get('shares', 0)
        
        if plays == 0:
            return 0.5
        
        # Calculate ratios
        like_ratio = likes / plays if plays > 0 else 0
        comment_ratio = comments / plays if plays > 0 else 0
        share_ratio = shares / plays if plays > 0 else 0
        
        # Comments and shares indicate higher engagement quality
        quality_score = (
            like_ratio * 0.3 +
            comment_ratio * 0.4 +  # Comments weighted higher
            share_ratio * 0.3  # Shares indicate strong engagement
        )
        
        # Normalize to 0-1 range
        # Typical good engagement: 10% likes, 1% comments, 0.5% shares
        normalized = min(1.0, quality_score * 10)
        
        return normalized
    
    def _find_matched_tags(
        self,
        video: Dict[str, Any],
        user_tags: List[Dict[str, Any]]
    ) -> List[str]:
        """Find which user tags match this video."""
        matched = []
        
        video_text = f"{video.get('description', '')} {' '.join(video.get('hashtags', []))}".lower()
        
        for tag in user_tags:
            tag_name = tag['tag'].lower()
            if tag_name in video_text or any(
                keyword in video_text for keyword in tag_name.split('_')
            ):
                matched.append(tag['tag'])
        
        # Also include source tags if available
        source_tags = video.get('source_tags', [])
        for tag in source_tags:
            if tag not in matched:
                matched.append(tag)
        
        return matched[:5]  # Return top 5 matches
    
    def _apply_diversity_boost(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity boost to prevent similar content clustering."""
        if len(recommendations) <= 10:
            return recommendations
        
        diverse_recs = []
        seen_authors = set()
        seen_tags = set()
        
        # First pass: Add top recommendations with diversity
        for rec in recommendations:
            author = rec['author']
            tags = set(rec['matched_tags'])
            
            # Check if too similar to already selected
            if author in seen_authors and len(diverse_recs) > 3:
                # Penalize repeated authors
                rec['score'] *= 0.9
            
            if tags and tags.issubset(seen_tags) and len(diverse_recs) > 5:
                # Penalize identical tag sets
                rec['score'] *= 0.85
            
            diverse_recs.append(rec)
            seen_authors.add(author)
            seen_tags.update(tags)
        
        # Re-sort after diversity adjustments
        diverse_recs.sort(key=lambda x: x['score'], reverse=True)
        
        return diverse_recs