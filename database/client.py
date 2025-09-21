"""Supabase database client."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client

from config import settings

class SupabaseClient:
    """Supabase database client."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase client."""
        try:
            if settings.supabase_url and settings.supabase_key:
                self.client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
            else:
                print("Warning: Supabase credentials not configured")
        except Exception as e:
            print(f"Error initializing Supabase: {e}")
            self.client = None
    
    def save_category(self, category: Dict[str, Any]):
        """Save category to database."""
        if not self.client:
            return
        
        try:
            data = {
                'tag': category['tag'],
                'description': category['description'],
                'keywords': category.get('keywords', []),
                'embedding': category.get('embedding'),
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('categories').upsert(data).execute()
        except Exception as e:
            print(f"Error saving category: {e}")
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories from database."""
        if not self.client:
            return []
        
        try:
            response = self.client.table('categories').select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
    
    def save_user_profile(self, profile: Dict[str, Any]):
        """Save user profile to database."""
        if not self.client:
            return
        
        try:
            # Save user data
            user_data = {
                'username': profile['username'],
                'user_id': profile.get('user_id'),
                'sec_uid': profile.get('sec_uid'),
                'bio': profile.get('bio'),
                'follower_count': profile.get('follower_count', 0),
                'following_count': profile.get('following_count', 0),
                'video_count': profile.get('video_count', 0),
                'updated_at': datetime.now().isoformat()
            }
            
            self.client.table('user_profiles').upsert(user_data).execute()
            
            # Save user tags
            for tag_info in profile.get('tags', []):
                tag_data = {
                    'username': profile['username'],
                    'tag': tag_info['tag'],
                    'affinity': tag_info['affinity'],
                    'reason': tag_info.get('reason', ''),
                    'updated_at': datetime.now().isoformat()
                }
                
                self.client.table('user_tags').upsert(tag_data).execute()
                
        except Exception as e:
            print(f"Error saving user profile: {e}")
    
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile from database."""
        if not self.client:
            return None
        
        try:
            # Get user data
            user_response = self.client.table('user_profiles') \
                .select("*") \
                .eq('username', username) \
                .single() \
                .execute()
            
            if not user_response.data:
                return None
            
            profile = user_response.data
            
            # Get user tags
            tags_response = self.client.table('user_tags') \
                .select("*") \
                .eq('username', username) \
                .order('affinity', desc=True) \
                .execute()
            
            profile['tags'] = tags_response.data
            
            return profile
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def save_recommendations(self, username: str, recommendations: List[Dict[str, Any]]):
        """Save recommendations to database."""
        if not self.client:
            return
        
        try:
            for rec in recommendations:
                data = {
                    'username': username,
                    'video_id': rec['video_id'],
                    'description': rec['description'],
                    'author': rec['author'],
                    'url': rec['url'],
                    'score': rec['score'],
                    'virality_score': rec['scores'].get('virality', 0),
                    'relevance_score': rec['scores'].get('relevance', 0),
                    'engagement_score': rec['scores'].get('engagement', 0),
                    'matched_tags': rec.get('matched_tags', []),
                    'created_at': datetime.now().isoformat()
                }
                
                self.client.table('recommendations').insert(data).execute()
                
        except Exception as e:
            print(f"Error saving recommendations: {e}")
    
    def save_result(self, pipeline: str, key: str, data: Any, metadata: Dict[str, Any] = None):
        """Save pipeline result to database."""
        if not self.client:
            return
        
        try:
            result_data = {
                'pipeline': pipeline,
                'key': key,
                'data': data,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('pipeline_results').upsert(result_data).execute()
            
        except Exception as e:
            print(f"Error saving result: {e}")
    
    def load_result(self, pipeline: str, key: str) -> Optional[Any]:
        """Load pipeline result from database."""
        if not self.client:
            return None
        
        try:
            response = self.client.table('pipeline_results') \
                .select("data") \
                .eq('pipeline', pipeline) \
                .eq('key', key) \
                .single() \
                .execute()
            
            if response.data:
                return response.data['data']
            
            return None
            
        except Exception as e:
            print(f"Error loading result: {e}")
            return None