"""Relevance scoring stage."""

from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils.embeddings import EmbeddingGenerator

class RelevanceScorer:
    """Score videos for relevance to user tags."""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
    
    def score_batch(
        self,
        videos: List[Dict[str, Any]],
        user_tags: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Score multiple videos for relevance.
        
        Args:
            videos: List of video dictionaries
            user_tags: List of user tags with affinity scores
            
        Returns:
            Dictionary mapping video ID to relevance score
        """
        scores = {}
        
        # Create user interest embedding
        user_embedding = self._create_user_embedding(user_tags)
        
        for video in videos:
            video_id = video.get('id')
            if video_id:
                scores[video_id] = self.score_single(video, user_tags, user_embedding)
        
        return scores
    
    def score_single(
        self,
        video: Dict[str, Any],
        user_tags: List[Dict[str, Any]],
        user_embedding: np.ndarray = None
    ) -> float:
        """
        Calculate relevance score for a single video.
        
        Args:
            video: Video dictionary
            user_tags: List of user tags with affinity scores
            user_embedding: Pre-computed user embedding
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # Create video text representation
        video_text = self._create_video_text(video)
        
        # Calculate tag match score
        tag_match_score = self._calculate_tag_match(video, user_tags)
        
        # Calculate embedding similarity
        if user_embedding is not None:
            video_embedding = self.embedding_generator.generate(video_text)
            if video_embedding is not None:
                similarity = cosine_similarity(
                    [user_embedding],
                    [video_embedding]
                )[0][0]
                # Normalize similarity to 0-1 range
                embedding_score = (similarity + 1) / 2
            else:
                embedding_score = 0.5
        else:
            embedding_score = 0.5
        
        # Check if video matches source query tags
        source_tag_boost = 0
        source_tags = video.get('source_tags', [])
        for tag in user_tags[:5]:  # Check top 5 user tags
            if tag['tag'] in source_tags:
                source_tag_boost = 0.2 * tag['affinity']
                break
        
        # Combine scores
        relevance_score = (
            tag_match_score * 0.4 +
            embedding_score * 0.4 +
            source_tag_boost * 0.2
        )
        
        return min(1.0, relevance_score)
    
    def _create_user_embedding(self, user_tags: List[Dict[str, Any]]) -> np.ndarray:
        """Create embedding representing user interests."""
        if not user_tags:
            return None
        
        # Create weighted text representation
        text_parts = []
        for tag in user_tags[:10]:  # Use top 10 tags
            # Repeat tag based on affinity (higher affinity = more repetitions)
            repetitions = max(1, int(tag['affinity'] * 3))
            for _ in range(repetitions):
                text_parts.append(tag['tag'])
                if tag.get('reason'):
                    text_parts.append(tag['reason'])
        
        user_text = ' '.join(text_parts)
        return self.embedding_generator.generate(user_text)
    
    def _create_video_text(self, video: Dict[str, Any]) -> str:
        """Create text representation of video."""
        parts = []
        
        # Add description
        if video.get('description'):
            parts.append(video['description'])
        
        # Add hashtags
        hashtags = video.get('hashtags', [])
        if hashtags:
            parts.append(' '.join([f"#{tag}" for tag in hashtags]))
        
        # Add music info
        if video.get('music_title'):
            parts.append(f"Music: {video['music_title']}")
        
        # Add author
        if video.get('author'):
            parts.append(f"By @{video['author']}")
        
        return ' '.join(parts)
    
    def _calculate_tag_match(
        self,
        video: Dict[str, Any],
        user_tags: List[Dict[str, Any]]
    ) -> float:
        """Calculate tag matching score."""
        video_text_lower = self._create_video_text(video).lower()
        
        total_score = 0
        max_possible = 0
        
        for tag in user_tags[:10]:  # Check top 10 user tags
            tag_name = tag['tag'].lower()
            affinity = tag['affinity']
            max_possible += affinity
            
            # Check for tag presence
            if tag_name in video_text_lower:
                total_score += affinity
            # Partial credit for related terms
            elif any(keyword in video_text_lower for keyword in tag_name.split('_')):
                total_score += affinity * 0.5
        
        if max_possible > 0:
            return total_score / max_possible
        
        return 0