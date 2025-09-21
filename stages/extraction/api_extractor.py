"""API data extraction stage."""

from typing import List, Dict, Any, Optional

from core.api_client import TikTokAPIClient

class APIExtractor:
    """Extract data from TikTok API."""
    
    def __init__(self):
        self.api_client = TikTokAPIClient()
    
    def extract_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Extract user profile data.
        
        Args:
            username: TikTok username
            
        Returns:
            User data dictionary or None if failed
        """
        user_info = self.api_client.get_user_info(username)
        
        if not user_info:
            return None
        
        user = user_info.get("user", {})
        stats = user_info.get("stats", {})
        
        return {
            'username': username,
            'user_id': user.get("id"),
            'sec_uid': user.get("secUid"),
            'nickname': user.get("nickname"),
            'bio': user.get("signature", ""),
            'verified': user.get("verified", False),
            'avatar': user.get("avatarLarger"),
            'follower_count': stats.get("followerCount", 0),
            'following_count': stats.get("followingCount", 0),
            'heart_count': stats.get("heartCount", 0),
            'video_count': stats.get("videoCount", 0)
        }
    
    def extract_user_posts(self, sec_uid: str, count: int = 30) -> List[Dict[str, Any]]:
        """
        Extract user's posted videos.
        
        Args:
            sec_uid: User's secure ID
            count: Number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        posts = self.api_client.get_user_posts(sec_uid, count)
        
        parsed_posts = []
        for post in posts:
            parsed = self._parse_post(post)
            if parsed:
                parsed_posts.append(parsed)
        
        return parsed_posts
    
    def extract_user_liked_posts(self, sec_uid: str, count: int = 30) -> List[Dict[str, Any]]:
        """
        Extract videos liked by user.
        
        Args:
            sec_uid: User's secure ID
            count: Number of liked posts to fetch
            
        Returns:
            List of liked post dictionaries
        """
        liked = self.api_client.get_user_liked_posts(sec_uid, count)
        
        parsed_liked = []
        for post in liked:
            parsed = self._parse_post(post)
            if parsed:
                parsed_liked.append(parsed)
        
        return parsed_liked
    
    def search_videos(self, query: str, count: int = 20) -> List[Dict[str, Any]]:
        """
        Search for videos.
        
        Args:
            query: Search query
            count: Number of videos to fetch
            
        Returns:
            List of video dictionaries
        """
        videos = self.api_client.search_videos(query, count)
        
        parsed_videos = []
        for video in videos:
            parsed = self._parse_post(video)
            if parsed:
                parsed_videos.append(parsed)
        
        return parsed_videos
    
    def extract_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive user profile data."""
        # Try to get detailed info with region first
        user_info = self.api_client.get_user_info_with_region(username)
        
        if not user_info:
            # Fallback to basic info
            user_info = self.api_client.get_user_info(username)
        
        if not user_info:
            return None
        
        user = user_info.get("user", {})
        stats = user_info.get("stats", {})
        stats_v2 = user_info.get("statsV2", {})
        
        return {
            'username': username,
            'user_id': user.get("id"),
            'sec_uid': user.get("secUid"),
            'nickname': user.get("nickname"),
            'bio': user.get("signature", ""),
            'verified': user.get("verified", False),
            'avatar': user.get("avatarLarger"),
            'follower_count': int(stats_v2.get("followerCount", stats.get("followerCount", 0))),
            'following_count': int(stats_v2.get("followingCount", stats.get("followingCount", 0))),
            'heart_count': int(stats_v2.get("heartCount", stats.get("heartCount", 0))),
            'video_count': int(stats_v2.get("videoCount", stats.get("videoCount", 0))),
            'region': user.get("region", "Unknown"),
            'language': user.get("language", "en"),
            'is_organization': user.get("isOrganization", 0) == 1,
            'category': user.get("commerceUserInfo", {}).get("category", None),
            'bio_link': user.get("bioLink", {}).get("link", None)
        }

    def extract_user_reposts(self, sec_uid: str, count: int = 30) -> List[Dict[str, Any]]:
        """Extract user's reposted videos."""
        reposts = self.api_client.get_user_reposts(sec_uid, count)
        
        parsed_reposts = []
        for repost in reposts:
            parsed = self._parse_post(repost)
            if parsed:
                parsed['is_repost'] = True
                parsed_reposts.append(parsed)
        
        return parsed_reposts
    
    def _parse_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse raw post data.
        
        Args:
            post_data: Raw post data from API
            
        Returns:
            Parsed post dictionary or None if failed
        """
        try:
            video = post_data.get("video", {})
            stats = post_data.get("stats", {})
            author = post_data.get("author", {})
            music = post_data.get("music", {})
            
            # Extract hashtags
            desc = post_data.get("desc", "")
            import re
            hashtags = re.findall(r'#(\w+)', desc)
            
            return {
                'id': post_data.get("id"),
                'description': desc,
                'create_time': post_data.get("createTime"),
                'author': author.get("uniqueId", ""),
                'author_nickname': author.get("nickname", ""),
                'author_id': author.get("id"),
                'music_title': music.get("title", ""),
                'music_author': music.get("authorName", ""),
                'duration': video.get("duration", 0),
                'cover': video.get("cover"),
                'play_url': video.get("playAddr"),
                'stats': {
                    'plays': stats.get("playCount", 0),
                    'likes': stats.get("diggCount", 0),
                    'comments': stats.get("commentCount", 0),
                    'shares': stats.get("shareCount", 0)
                },
                'hashtags': hashtags,
                'url': f"https://www.tiktok.com/@{author.get('uniqueId')}/video/{post_data.get('id')}"
            }
        except Exception as e:
            print(f"Error parsing post: {e}")
            return None