"""Affinity scoring stage."""

from typing import List, Dict, Any

class AffinityScorer:
    """Score user-tag affinity."""
    
    def score(
        self,
        tag_mappings: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        posts: List[Dict[str, Any]],
        liked_posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate final affinity scores for tags.
        
        Args:
            tag_mappings: Initial tag mappings from LLM
            user_data: User profile data
            posts: User's posted videos
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
                tag, posts, liked_posts
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
        liked_posts: List[Dict[str, Any]]
    ) -> float:
        """Calculate engagement-based boost for a tag."""
        boost = 0.0
        
        # Check how many posts/likes relate to this tag
        tag_lower = tag.lower()
        relevant_posts = 0
        total_engagement = 0
        
        for post in posts:
            desc_lower = post.get('description', '').lower()
            hashtags_lower = [h.lower() for h in post.get('hashtags', [])]
            
            if tag_lower in desc_lower or tag_lower in hashtags_lower:
                relevant_posts += 1
                stats = post.get('stats', {})
                total_engagement += (
                    stats.get('likes', 0) +
                    stats.get('comments', 0) * 2 +  # Comments weighted higher
                    stats.get('shares', 0) * 3  # Shares weighted highest
                )
        
        if relevant_posts > 0:
            avg_engagement = total_engagement / relevant_posts
            # Normalize to 0-0.2 boost range
            boost = min(0.2, avg_engagement / 100000)
        
        return boost
    
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