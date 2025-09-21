"""Tests for API client and schema validation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.api_client import TikTokAPIClient
from core.models import Video, UserProfile, APIResponse

class TestAPIClient:
    """Test TikTok API client."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TikTokAPIClient()
    
    def test_api_response_schema(self):
        """Test API response model schema."""
        response = APIResponse(
            status_code=200,
            data={"test": "data"},
            error=None,
            cached=False
        )
        
        assert response.status_code == 200
        assert response.data == {"test": "data"}
        assert response.error is None
        assert response.cached is False
    
    def test_video_model_schema(self):
        """Test video model schema."""
        video = Video(
            id="123456",
            description="Test video #test",
            author="testuser",
            create_time=1234567890,
            url="https://tiktok.com/test",
            stats={"plays": 1000, "likes": 100}
        )
        
        assert video.id == "123456"
        assert video.description == "Test video #test"
        assert video.author == "testuser"
        assert video.hashtags == []  # Default empty list
        assert video.stats["plays"] == 1000
    
    def test_user_profile_model(self):
        """Test user profile model."""
        profile = UserProfile(
            username="testuser",
            bio="Test bio",
            follower_count=1000,
            tags=[
                {"tag": "dance", "affinity": 0.8}
            ]
        )
        
        assert profile.username == "testuser"
        assert profile.bio == "Test bio"
        assert profile.follower_count == 1000
        assert len(profile.tags) == 1
        assert profile.tags[0]["tag"] == "dance"
    
    @patch('requests.get')
    def test_get_user_info_success(self, mock_get):
        """Test successful user info retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userInfo": {
                "user": {
                    "id": "123",
                    "uniqueId": "testuser",
                    "nickname": "Test User",
                    "secUid": "sec123",
                    "signature": "Test bio"
                },
                "stats": {
                    "followerCount": 1000,
                    "followingCount": 500,
                    "heartCount": 10000,
                    "videoCount": 50
                }
            }
        }
        mock_get.return_value = mock_response
        
        # Test
        result = self.client.get_user_info("testuser")
        
        assert result is not None
        assert result["user"]["uniqueId"] == "testuser"
        assert result["stats"]["followerCount"] == 1000
    
    @patch('requests.get')
    def test_get_user_info_failure(self, mock_get):
        """Test failed user info retrieval."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "User not found"
        mock_get.return_value = mock_response
        
        # Test
        result = self.client.get_user_info("nonexistent")
        
        assert result is None
    
    @patch('requests.get')
    def test_search_videos_pagination(self, mock_get):
        """Test video search with pagination."""
        # Mock paginated responses
        responses = [
            {
                "item_list": [
                    {"id": f"video{i}", "desc": f"Video {i}"}
                    for i in range(10)
                ],
                "has_more": True,
                "cursor": "10",
                "log_pb": {"impr_id": "search123"}
            },
            {
                "item_list": [
                    {"id": f"video{i}", "desc": f"Video {i}"}
                    for i in range(10, 15)
                ],
                "has_more": False,
                "cursor": "15"
            }
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        mock_response.json.side_effect = responses
        
        # Test
        videos = self.client.search_videos("test", count=15)
        
        assert len(videos) == 15
        assert videos[0]["id"] == "video0"
        assert videos[14]["id"] == "video14"
    
    def test_parse_video(self):
        """Test video parsing."""
        raw_video = {
            "id": "123456",
            "desc": "Test video #dance #fun",
            "createTime": 1234567890,
            "video": {
                "duration": 30,
                "height": 1920,
                "width": 1080,
                "cover": "https://cover.jpg",
                "playAddr": "https://play.mp4"
            },
            "author": {
                "id": "789",
                "uniqueId": "testuser",
                "nickname": "Test User"
            },
            "music": {
                "title": "Test Song",
                "authorName": "Artist"
            },
            "stats": {
                "playCount": 10000,
                "diggCount": 1000,
                "commentCount": 100,
                "shareCount": 50
            }
        }
        
        # Test
        video = self.client.parse_video(raw_video)
        
        assert video.id == "123456"
        assert video.description == "Test video #dance #fun"
        assert video.author == "testuser"
        assert video.duration == 30
        assert video.stats["plays"] == 10000
        assert video.stats["likes"] == 1000
        assert "dance" in video.hashtags
        assert "fun" in video.hashtags
    
    def test_extract_hashtags(self):
        """Test hashtag extraction."""
        text = "Check this out! #dance #TikTok #viral2024 #"
        hashtags = self.client._extract_hashtags(text)
        
        assert "dance" in hashtags
        assert "TikTok" in hashtags
        assert "viral2024" in hashtags
        assert len(hashtags) == 3
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        import time
        from config import settings
        
        # Record start time
        start_time = time.time()
        
        # Make two rate-limited calls
        self.client._rate_limit()
        self.client._rate_limit()
        
        # Check that appropriate delay was applied
        elapsed = time.time() - start_time
        assert elapsed >= settings.rate_limit_delay