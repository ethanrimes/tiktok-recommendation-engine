"""Pipeline for generating recommendations."""

from typing import List, Dict, Any

from pipelines.base import BasePipeline
from stages.transformation.query_generator import QueryGenerator
from stages.extraction.api_extractor import APIExtractor
from stages.scoring.virality_scorer import ViralityScorer
from stages.scoring.relevance_scorer import RelevanceScorer
from stages.scoring.final_ranker import FinalRanker
from config import settings

class RecommendationPipeline(BasePipeline):
    """Pipeline to generate video recommendations."""
    
    def __init__(self):
        super().__init__(name="recommendation")
        self.query_generator = QueryGenerator()
        self.api_extractor = APIExtractor()
        self.virality_scorer = ViralityScorer()
        self.relevance_scorer = RelevanceScorer()
        self.final_ranker = FinalRanker()
    
    def run(self, user_profile: Dict[str, Any], count: int = 20) -> List[Dict[str, Any]]:
        """
        Run the recommendation pipeline.
        
        Args:
            user_profile: User profile with tags
            count: Number of recommendations to generate
            
        Returns:
            List of recommended videos
        """
        self.start()
        
        try:
            # Step 1: Generate search queries from user tags
            self.log("Generating search queries...")
            queries = self.query_generator.generate(
                user_tags=user_profile['tags'],
                num_queries=settings.max_search_queries
            )
            self.log(f"Generated {len(queries)} search queries")
            
            # Step 2: Fetch videos for each query
            self.log("Fetching videos...")
            all_videos = []
            seen_ids = set()
            
            for query in queries:
                self.log(f"Searching for: {query['query']}")
                videos = self.api_extractor.search_videos(
                    query=query['query'],
                    count=settings.videos_per_query
                )
                
                # Deduplicate
                for video in videos:
                    if video['id'] not in seen_ids:
                        seen_ids.add(video['id'])
                        video['source_query'] = query['query']
                        video['source_tags'] = query.get('source_tags', [])
                        all_videos.append(video)
            
            self.log(f"Fetched {len(all_videos)} unique videos")
            
            if not all_videos:
                self.log("No videos found", "warning")
                self.end()
                return []
            
            # Step 3: Score videos for virality
            self.log("Scoring videos for virality...")
            virality_scores = self.virality_scorer.score_batch(all_videos)
            
            # Step 4: Score videos for relevance
            self.log("Scoring videos for relevance...")
            relevance_scores = self.relevance_scorer.score_batch(
                videos=all_videos,
                user_tags=user_profile['tags']
            )
            
            # Step 5: Combine scores and rank
            self.log("Ranking videos...")
            recommendations = self.final_ranker.rank(
                videos=all_videos,
                virality_scores=virality_scores,
                relevance_scores=relevance_scores,
                user_profile=user_profile
            )
            
            # Filter by minimum score
            recommendations = [
                rec for rec in recommendations
                if rec['score'] >= settings.min_video_score
            ]
            
            # Limit to requested count
            recommendations = recommendations[:count]
            
            self.log(f"Generated {len(recommendations)} recommendations")
            
            # Step 6: Save recommendations
            self.log("Saving recommendations to database...")
            self.db_client.save_recommendations(
                username=user_profile['username'],
                recommendations=recommendations
            )
            
            # Save complete result
            self.save_result(
                recommendations,
                f"recommendations_{user_profile['username']}_{count}"
            )
            
            self.end()
            return recommendations
            
        except Exception as e:
            self.log(f"Pipeline failed: {e}", "error")
            self.end()
            return []