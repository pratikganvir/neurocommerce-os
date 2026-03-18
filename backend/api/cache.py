"""Cache and Redis utilities"""
import os
import json
import redis
from typing import Any, Optional

# Redis client
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)


def set_cache(key: str, value: Any, expire_seconds: int = 3600) -> bool:
    """Set a value in cache"""
    try:
        redis_client.setex(key, expire_seconds, json.dumps(value))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache"""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


def delete_cache(key: str) -> bool:
    """Delete a cache key"""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def clear_cache_pattern(pattern: str) -> int:
    """Clear all keys matching a pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache clear error: {e}")
        return 0


class CacheManager:
    """Context manager for cache operations"""
    
    def __init__(self, key: str, expire_seconds: int = 3600):
        self.key = key
        self.expire_seconds = expire_seconds
    
    def get(self) -> Optional[Any]:
        return get_cache(self.key)
    
    def set(self, value: Any) -> bool:
        return set_cache(self.key, value, self.expire_seconds)
    
    def delete(self) -> bool:
        return delete_cache(self.key)
