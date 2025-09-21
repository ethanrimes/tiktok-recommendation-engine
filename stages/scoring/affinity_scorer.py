"""Affinity scoring stage."""

from typing import List, Dict, Any

class AffinityScorer:
    """Score user-tag affinity."""
    
    def score(
        self,
        tag_mappings: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        posts: List[Dict[str, Any]],
        reposts: List[Dict[str, Any]],  # ADDED: reposts parameter
        liked_posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate final affinity scores for tags.
        
        Args:
            tag_mappings: Initial tag mappings from LLM
            user_data: User profile data
            posts: User's posted videos
            reposts: User's reposted videos  # ADDED
            liked_posts: Videos liked by user
            
        Returns:
            List of tags with adjusted affinity scores
        """
        scored_tags = []
        
        for mapping in tag_mappings:
            tag = mapping['tag']
            base_affinity = mapping.get('affinity', 0.5)
            
            # Adjust based on engagement patterns
            engagement_boost = self._calculate_engagement_boost(
                tag, posts, reposts, liked_posts  # FIXED: Added reposts
            )
            
            # Adjust based on user influence
            influence_factor = self._calculate_influence_factor(user_data)
            
            # Calculate final score
            final_affinity = min(1.0, base_affinity + engagement_boost * influence_factor)
            
            scored_tags.append({
                'tag': tag,
                'affinity': final_affinity,
                'reason': mapping.get('reason', ''),
                'base_affinity': base_affinity,
                'engagement_boost': engagement_boost
            })
        
        return scored_tags
    
    def _calculate_engagement_boost(
        self,
        tag: str,
        posts: List[Dict[str, Any]],
        reposts: List[Dict[str, Any]],  # Parameter already correct
        liked_posts: List[Dict[str, Any]]
    ) -> float:
        """Calculate engagement-based boost for a tag."""
        boost = 0.0
        tag_lower = tag.lower()
        
        # Analyze posts
        post_relevance = self._analyze_content_relevance(posts, tag_lower, weight=1.0)
        
        # Analyze reposts (weighted slightly lower than original posts)
        repost_relevance = self._analyze_content_relevance(reposts, tag_lower, weight=0.8)
        
        # Analyze liked posts (weighted lower)
        liked_relevance = self._analyze_content_relevance(liked_posts, tag_lower, weight=0.6)
        
        # Combine scores
        total_relevance = post_relevance + repost_relevance + liked_relevance
        
        # Normalize to 0-0.2 boost range
        boost = min(0.2, total_relevance / 100)
        
        return boost
    
    def _analyze_content_relevance(self, content: List[Dict[str, Any]], tag: str, weight: float) -> float:
        """Analyze how relevant content is to a tag."""
        if not content:
            return 0.0
        
        relevance_score = 0.0
        for item in content:
            desc_lower = item.get('description', '').lower()
            hashtags_lower = [h.lower() for h in item.get('hashtags', [])]
            
            if tag in desc_lower or tag in hashtags_lower:
                stats = item.get('stats', {})
                engagement = (
                    stats.get('likes', 0) +
                    stats.get('comments', 0) * 2 +
                    stats.get('shares', 0) * 3
                )
                relevance_score += engagement * weight
        
        return relevance_score

    def _calculate_influence_factor(self, user_data: Dict[str, Any]) -> float:
        """Calculate user influence factor."""
        followers = user_data.get('follower_count', 0)
        
        if followers < 1000:
            return 0.8
        elif followers < 10000:
            return 0.9
        elif followers < 100000:
            return 1.0
        elif followers < 1000000:
            return 1.1
        else:
            return 1.2