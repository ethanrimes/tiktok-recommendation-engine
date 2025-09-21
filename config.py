"""Configuration settings for TikTok Recommendation Engine."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    rapidapi_key: str = os.getenv("RAPIDAPI_KEY", "")
    rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "tiktok-api23.p.rapidapi.com")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Supabase Configuration - Match your actual env vars
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")  # Changed from supabase_key
    
    # Optional: Add these if you want to keep them available
    supabase_db_url: Optional[str] = os.getenv("SUPABASE_DB_URL", "")
    supabase_db_password: Optional[str] = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    # Directory Configuration
    base_dir: Path = Path(__file__).parent
    data_dir: Path = base_dir / "data"
    cache_dir: Path = data_dir / "cache"
    output_dir: Path = data_dir / "output"
    input_dir: Path = data_dir / "input"
    prompts_dir: Path = base_dir / "prompts"
    
    # API Settings
    max_api_retries: int = 3
    api_timeout: int = 30
    rate_limit_delay: float = 1.0  # seconds between API calls
    
    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    enable_cache: bool = True
    
    # Taxonomy Generation Settings
    num_categories: int = 100
    min_category_confidence: float = 0.7
    
    # User Profiling Settings
    max_posts_to_analyze: int = 50
    max_liked_posts: int = 30
    min_tag_affinity: float = 0.3
    
    # Recommendation Settings
    max_search_queries: int = 10
    videos_per_query: int = 20
    min_video_score: float = 0.5
    
    # Ranking Weights
    virality_weight: float = 0.3
    engagement_weight: float = 0.3
    relevance_weight: float = 0.4
    
    # Model Settings
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4.1"
    llm_temperature: float = 0.7
    
    # Logging
    log_level: str = "INFO"
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        for dir_path in [self.data_dir, self.cache_dir, self.output_dir, self.input_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

# Create global settings instance
settings = Settings()
settings.create_directories()