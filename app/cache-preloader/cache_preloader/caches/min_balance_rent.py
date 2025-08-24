from datetime import timedelta

import aioredis
from cache_preloader.core.base import BaseAutoUpdateCache
from solbot_cache.constants import MIN_BALANCE_RENT_CACHE_KEY
from solbot_common.log import logger
from solbot_common.utils import get_async_client
from solbot_db.redis import RedisClient
from spl.token.async_client import AsyncToken


class MinBalanceRentCache(BaseAutoUpdateCache):
    """Minimum Balance Rent Cache Manager"""

    key = MIN_BALANCE_RENT_CACHE_KEY

    def __init__(self, redis: aioredis.Redis):
        """
        Initialize minimum balance rent cache manager

        Args:
            redis: Redis client instance
        """
        self.client = get_async_client()
        self.redis = redis
        super().__init__(redis)

    async def _gen_new_value(self) -> int:
        """
        Generate new cache value

        Returns:
            Minimum balance rent
        """
        min_balance = await AsyncToken.get_min_balance_rent_for_exempt_for_account(self.client)
        return min_balance

    @classmethod
    async def get(cls, redis: aioredis.Redis | None = None) -> int:
        """
        Get minimum balance rent

        Args:
            redis: Redis client instance, if None gets default instance

        Returns:
            Minimum balance rent
        """
        redis = redis or RedisClient.get_instance()
        cached_value = await redis.get(cls.key)
        if cached_value is None:
            logger.warning("Minimum balance rent cache not found, updating...")
            min_balance_rent_cache = cls(redis)
            cached_value = await min_balance_rent_cache._gen_new_value()
            await redis.set(cls.key, cached_value, ex=timedelta(seconds=30))
        return int(cached_value)
