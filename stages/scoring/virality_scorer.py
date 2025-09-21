"""Virality scoring stage."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class ViralityScorer:
    """Score videos for virality."""
    
    def score_batch(self, videos: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Score multiple videos for virality.
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            Dictionary mapping video ID to virality score
        """
        scores = {}
        
        for video in videos:
            video_id = video.get('id')
            if video_id:
                scores[video_id] = self.score_single(video)
        
        return scores
    
    def score_single(self, video: Dict[str, Any]) -> float:
        """
        Calculate virality score for a single video.
        
        Args:
            video: Video dictionary
            
        Returns:
            Virality score (0.0 to 1.0)
        """
        stats = video.get('stats', {})
        
        # Get engagement metrics
        plays = stats.get('plays', 0)
        likes = stats.get('likes', 0)
        comments = stats.get('comments', 0)
        shares = stats.get('shares', 0)
        
        # Calculate engagement rate
        engagement_rate = 0
        if plays > 0:
            total_engagement = likes + comments + shares
            engagement_rate = total_engagement / plays
        
        # Score components
        play_score = self._normalize_plays(plays)
        engagement_score = self._normalize_engagement_rate(engagement_rate)
        share_score = self._normalize_shares(shares)
        
        # Time decay factor
        time_factor = self._calculate_time_decay(video.get('create_time'))
        
        # Weighted combination
        virality_score = (
            play_score * 0.3 +
            engagement_score * 0.3 +
            share_score * 0.2 +
            time_factor * 0.2
        )
        
        return min(1.0, virality_score)
    
    def _normalize_plays(self, plays: int) -> float:
        """Normalize play count to 0-1 scale."""
        if plays < 10000:
            return plays / 10000 * 0.3
        elif plays < 100000:
            return 0.3 + (plays - 10000) / 90000 * 0.3
        elif plays < 1000000:
            return 0.6 + (plays - 100000) / 900000 * 0.2
        elif plays < 10000000:
            return 0.8 + (plays - 1000000) / 9000000 * 0.15
        else:
            return 0.95 + min(0.05, plays / 100000000)
    
    def _normalize_engagement_rate(self, rate: float) -> float:
        """Normalize engagement rate to 0-1 scale."""
        # Typical engagement rates: 1-5% is good, 5-10% is excellent, >10% is viral
        if rate < 0.01:
            return rate / 0.01 * 0.3
        elif rate < 0.05:
            return 0.3 + (rate - 0.01) / 0.04 * 0.3
        elif rate < 0.10:
            return 0.6 + (rate - 0.05) / 0.05 * 0.25
        elif rate < 0.20:
            return 0.85 + (rate - 0.10) / 0.10 * 0.1
        else:
            return 0.95 + min(0.05, rate - 0.20)
    
    def _normalize_shares(self, shares: int) -> float:
        """Normalize share count to 0-1 scale."""
        if shares < 100:
            return shares / 100 * 0.3
        elif shares < 1000:
            return 0.3 + (shares - 100) / 900 * 0.3
        elif shares < 10000:
            return 0.6 + (shares - 1000) / 9000 * 0.25
        elif shares < 100000:
            return 0.85 + (shares - 10000) / 90000 * 0.1
        else:
            return 0.95 + min(0.05, shares / 1000000)
    
    def _calculate_time_decay(self, create_time: int) -> float:
        """Calculate time decay factor."""
        if not create_time:
            return 0.5
        
        try:
            video_date = datetime.fromtimestamp(create_time)
            days_old = (datetime.now() - video_date).days
            
            if days_old < 1:
                return 1.0
            elif days_old < 7:
                return 0.9
            elif days_old < 30:
                return 0.7
            elif days_old < 90:
                return 0.5
            elif days_old < 180:
                return 0.3
            else:
                return 0.1
        except:
            return 0.5