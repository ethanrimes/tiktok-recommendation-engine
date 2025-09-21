"""Pipeline for user profiling."""

from typing import List, Dict, Any

from pipelines.base import BasePipeline
from stages.extraction.api_extractor import APIExtractor
from stages.transformation.tag_mapper import TagMapper
from stages.scoring.affinity_scorer import AffinityScorer
from core.models import UserProfile
from config import settings

class ProfilingPipeline(BasePipeline):
    """Pipeline to generate user profile with category tags."""
    
    def __init__(self):
        super().__init__(name="profiling")
        self.api_extractor = APIExtractor()
        self.tag_mapper = TagMapper()
        self.affinity_scorer = AffinityScorer()
    
    def run(self, username: str, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the user profiling pipeline.
        
        Args:
            username: TikTok username
            categories: List of available categories
            
        Returns:
            User profile dictionary with tags and affinity scores
        """
        self.start()
        
        try:
            # Step 1: Extract user data from API
            self.log(f"Fetching data for user @{username}...")
            user_data = self.api_extractor.extract_user_data(username)
            
            if not user_data:
                self.log(f"Could not fetch data for user @{username}", "error")
                return {}
            
            self.log(f"Fetched profile: {user_data.get('video_count', 0)} posts, {user_data.get('follower_count', 0)} followers")
            
            # Step 2: Fetch user's posts
            self.log("Fetching user's posts...")
            posts = self.api_extractor.extract_user_posts(
                user_data['sec_uid'],
                count=settings.max_posts_to_analyze
            )
            self.log(f"Fetched {len(posts)} posts")
            
            # Step 3: Fetch user's liked posts
            self.log("Fetching user's liked posts...")
            liked_posts = self.api_extractor.extract_user_liked_posts(
                user_data['sec_uid'],
                count=settings.max_liked_posts
            )
            self.log(f"Fetched {len(liked_posts)} liked posts")
            
            # Step 4: Map user data to categories
            self.log("Mapping user interests to categories...")
            tag_mappings = self.tag_mapper.map_tags(
                user_data=user_data,
                posts=posts,
                liked_posts=liked_posts,
                categories=categories
            )
            
            # Step 5: Calculate affinity scores
            self.log("Calculating affinity scores...")
            scored_tags = self.affinity_scorer.score(
                tag_mappings=tag_mappings,
                user_data=user_data,
                posts=posts,
                liked_posts=liked_posts
            )
            
            # Filter by minimum affinity
            scored_tags = [
                tag for tag in scored_tags 
                if tag['affinity'] >= settings.min_tag_affinity
            ]
            
            # Sort by affinity score
            scored_tags.sort(key=lambda x: x['affinity'], reverse=True)
            
            self.log(f"Identified {len(scored_tags)} relevant tags")
            
            # Step 6: Create user profile
            user_profile = {
                'username': username,
                'user_id': user_data.get('user_id'),
                'sec_uid': user_data.get('sec_uid'),
                'bio': user_data.get('bio'),
                'follower_count': user_data.get('follower_count', 0),
                'following_count': user_data.get('following_count', 0),
                'video_count': user_data.get('video_count', 0),
                'tags': scored_tags,
                'post_count_analyzed': len(posts),
                'liked_count_analyzed': len(liked_posts)
            }
            
            # Step 7: Save to database
            self.log("Saving user profile to database...")
            self.db_client.save_user_profile(user_profile)
            
            # Save complete result
            self.save_result(user_profile, f"profile_{username}")
            
            self.end()
            return user_profile
            
        except Exception as e:
            self.log(f"Pipeline failed: {e}", "error")
            self.end()
            return {}