"""Caching utilities."""

import json
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import diskcache

from config import settings

class CacheManager:
    """Manage caching for API responses and computations."""
    
    def __init__(self):
        cache_path = settings.cache_dir / "api_cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(cache_path))
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            return self.cache.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            expire = ttl or settings.cache_ttl
            self.cache.set(key, value, expire=expire)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete value from cache."""
        try:
            self.cache.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def clear(self):
        """Clear all cache."""
        try:
            self.cache.clear()
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a string representation of arguments
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Generate hash for the key
        return hashlib.md5(key_string.encode()).hexdigest()