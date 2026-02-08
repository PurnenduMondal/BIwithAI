import json
import redis.asyncio as redis
from typing import Any, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value:
                return json.loads(value)
            return None
        
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            client = await self.get_client()
            serialized = json.dumps(value, default=str)
            
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
            
            return True
        
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        
        except Exception as e:
            logger.error(f"Redis EXISTS error: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment integer value"""
        try:
            client = await self.get_client()
            return await client.incrby(key, amount)
        
        except Exception as e:
            logger.error(f"Redis INCREMENT error: {str(e)}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        try:
            client = await self.get_client()
            await client.expire(key, ttl)
            return True
        
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()