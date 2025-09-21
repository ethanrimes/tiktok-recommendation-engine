"""TikTok API client wrapper."""

import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from core.models import APIResponse, Video, UserProfile
from utils.cache import CacheManager

class TikTokAPIClient:
    """TikTok API client with caching and rate limiting."""
    
    def __init__(self):
        self.base_url = f"https://{settings.rapidapi_host}/api"
        self.headers = {
            "x-rapidapi-key": settings.rapidapi_key,
            "x-rapidapi-host": settings.rapidapi_host
        }
        self.cache = CacheManager() if settings.enable_cache else None
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.rate_limit_delay:
            time.sleep(settings.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(settings.max_api_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make API request with retries."""
        # Check cache first
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return APIResponse(
                    status_code=200,
                    data=cached_data,
                    cached=True
                )
        
        # Rate limiting
        self._rate_limit()
        
        # Make request
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=settings.api_timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Cache successful response
            if self.cache:
                self.cache.set(cache_key, data, ttl=settings.cache_ttl)
            
            return APIResponse(
                status_code=200,
                data=data,
                cached=False
            )
        else:
            return APIResponse(
                status_code=response.status_code,
                error=f"API error: {response.text}"
            )
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        response = self._make_request(
            "user/info",
            {"uniqueId": username}
        )
        
        if response.status_code == 200 and response.data:
            user_info = response.data.get("userInfo", {})
            return user_info
        return None
    
    def get_user_posts(self, sec_uid: str, count: int = 30, cursor: int = 0) -> List[Dict[str, Any]]:
        """Get user's posted videos."""
        posts = []
        
        while len(posts) < count:
            response = self._make_request(
                "user/posts",
                {
                    "secUid": sec_uid,
                    "count": min(30, count - len(posts)),
                    "cursor": cursor
                }
            )
            
            if response.status_code != 200 or not response.data:
                break
            
            data = response.data.get("data", {})
            item_list = data.get("itemList", [])
            
            if not item_list:
                break
            
            posts.extend(item_list)
            
            if not data.get("hasMore"):
                break
            
            cursor = data.get("cursor", cursor + len(item_list))
        
        return posts[:count]
    
    def get_user_liked_posts(self, sec_uid: str, count: int = 30, cursor: int = 0) -> List[Dict[str, Any]]:
        """Get videos liked by user."""
        liked = []
        
        while len(liked) < count:
            response = self._make_request(
                "user/liked-posts",
                {
                    "secUid": sec_uid,
                    "count": min(30, count - len(liked)),
                    "cursor": cursor
                }
            )
            
            if response.status_code != 200 or not response.data:
                break
            
            data = response.data.get("data", {})
            item_list = data.get("itemList", [])
            
            if not item_list:
                break
            
            liked.extend(item_list)
            
            if not data.get("hasMore"):
                break
            
            cursor = data.get("cursor", cursor + len(item_list))
        
        return liked[:count]
    
    def search_videos(self, keyword: str, count: int = 20) -> List[Dict[str, Any]]:
        """Search for videos by keyword."""
        videos = []
        cursor = "0"
        search_id = "0"
        
        while len(videos) < count:
            response = self._make_request(
                "search/video",
                {
                    "keyword": keyword,
                    "cursor": cursor,
                    "search_id": search_id,
                    "count": str(min(20, count - len(videos)))
                }
            )
            
            if response.status_code != 200 or not response.data:
                break
            
            item_list = response.data.get("item_list", response.data.get("itemList", []))
            
            if not item_list:
                break
            
            videos.extend(item_list)
            
            if not response.data.get("has_more", response.data.get("hasMore")):
                break
            
            cursor = response.data.get("cursor", cursor)
            log_pb = response.data.get("log_pb", {})
            search_id = log_pb.get("impr_id", search_id)
        
        return videos[:count]
    
    def get_trending_posts(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get trending videos."""
        response = self._make_request(
            "post/trending",
            {"count": str(count)}
        )
        
        if response.status_code == 200 and response.data:
            return response.data.get("itemList", [])
        return []
    
    def parse_video(self, video_data: Dict[str, Any]) -> Video:
        """Parse raw video data into Video model."""
        video_info = video_data.get("video", {})
        stats = video_data.get("stats", {})
        author = video_data.get("author", {})
        
        return Video(
            id=video_data.get("id", ""),
            description=video_data.get("desc", ""),
            author=author.get("uniqueId", ""),
            author_id=author.get("id"),
            music_title=video_data.get("music", {}).get("title"),
            duration=video_info.get("duration", 0),
            create_time=video_data.get("createTime", 0),
            stats={
                "plays": stats.get("playCount", 0),
                "likes": stats.get("diggCount", 0),
                "comments": stats.get("commentCount", 0),
                "shares": stats.get("shareCount", 0)
            },
            url=f"https://www.tiktok.com/@{author.get('uniqueId')}/video/{video_data.get('id')}",
            cover=video_info.get("cover"),
            hashtags=self._extract_hashtags(video_data.get("desc", ""))
        )
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        import re
        return re.findall(r'#(\w+)', text)