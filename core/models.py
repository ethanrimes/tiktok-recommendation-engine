"""Data models for TikTok Recommendation Engine."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class Category(BaseModel):
    """Content category model."""
    tag: str = Field(..., description="Category tag name")
    description: str = Field(..., description="Detailed description of the category")
    keywords: List[str] = Field(default_factory=list, description="Associated keywords")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the category")

class UserProfile(BaseModel):
    """User profile model."""
    username: str = Field(..., description="TikTok username")
    user_id: Optional[str] = Field(None, description="TikTok user ID")
    sec_uid: Optional[str] = Field(None, description="TikTok secure user ID")
    bio: Optional[str] = Field(None, description="User bio")
    follower_count: int = Field(0, description="Number of followers")
    following_count: int = Field(0, description="Number of following")
    video_count: int = Field(0, description="Number of videos posted")
    tags: List[Dict[str, Any]] = Field(default_factory=list, description="Category tags with affinity scores")
    analyzed_at: datetime = Field(default_factory=datetime.now)

class Video(BaseModel):
    """Video model."""
    id: str = Field(..., description="Video ID")
    description: str = Field(..., description="Video caption/description")
    author: str = Field(..., description="Author username")
    author_id: Optional[str] = Field(None, description="Author user ID")
    music_title: Optional[str] = Field(None, description="Music/sound title")
    duration: int = Field(0, description="Video duration in seconds")
    create_time: int = Field(..., description="Creation timestamp")
    stats: Dict[str, int] = Field(default_factory=dict, description="Engagement statistics")
    url: str = Field(..., description="Video URL")
    cover: Optional[str] = Field(None, description="Cover image URL")
    hashtags: List[str] = Field(default_factory=list, description="Video hashtags")
    
class SearchQuery(BaseModel):
    """Search query model."""
    query: str = Field(..., description="Search query string")
    source_tags: List[str] = Field(default_factory=list, description="Tags that generated this query")
    weight: float = Field(1.0, description="Query weight/importance")

class Recommendation(BaseModel):
    """Video recommendation model."""
    video_id: str = Field(..., description="Video ID")
    description: str = Field(..., description="Video description")
    author: str = Field(..., description="Author username")
    url: str = Field(..., description="Video URL")
    score: float = Field(..., description="Recommendation score")
    scores: Dict[str, float] = Field(default_factory=dict, description="Individual score components")
    matched_tags: List[str] = Field(default_factory=list, description="Matched user tags")
    
class APIResponse(BaseModel):
    """Generic API response model."""
    status_code: int = Field(..., description="HTTP status code")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    cached: bool = Field(False, description="Whether response was from cache")