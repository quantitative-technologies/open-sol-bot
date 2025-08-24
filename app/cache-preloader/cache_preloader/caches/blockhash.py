from datetime import timedelta

import aioredis
import orjson as json
from cache_preloader.core.base import BaseAutoUpdateCache
from solbot_cache.constants import BLOCKHASH_CACHE_KEY
from solbot_common.log import logger
from solbot_common.utils import get_async_client
from solbot_db.redis import RedisClient
from solders.hash import Hash  # type: ignore


class BlockhashCache(BaseAutoUpdateCache):
    """Block hash cache manager"""

    key = BLOCKHASH_CACHE_KEY

    def __init__(self, redis: aioredis.Redis):
        """
        Initialize block hash cache manager

        Args:
            redis: Redis client instance
        """
        self.client = get_async_client()
        self.redis = redis
        super().__init__(redis)

    @classmethod
    async def _get_latest_blockhash(cls) -> tuple[Hash, int]:
        """
        Get the latest block hash

        Returns:
            Tuple of block hash and last valid block height
        """
        resp = await get_async_client().get_latest_blockhash()
        return resp.value.blockhash, resp.value.last_valid_block_height

    async def _gen_new_value(self) -> str:
        """
        Generate new cache value

        Returns:
            Serialized block hash information
        """
        _hash, _last_valid_block_height = await self._get_latest_blockhash()
        return json.dumps(
            {
                "blockhash": str(_hash),
                "last_valid_block_height": str(_last_valid_block_height),
            }
        ).decode("utf-8")

    @classmethod
    async def get(cls, redis: aioredis.Redis | None = None) -> tuple[Hash, int]:
        """
        Get the current block hash and last valid block height
        If available, use the cached value

        Args:
            redis: Redis client instance, if None, get the default instance

        Returns:
            Tuple of block hash and last valid block height
        """
        # if os.getenv("PYTEST_CURRENT_TEST"):
        # return await cls._get_latest_blockhash()

        redis = redis or RedisClient.get_instance()
        raw_cached_value = await redis.get(cls.key)
        if raw_cached_value is None:
            logger.warning("Block hash cache not found, updating...")
            blockhash_cache = cls(redis)
            raw_cached_value = await blockhash_cache._gen_new_value()
            await redis.set(cls.key, raw_cached_value, ex=timedelta(seconds=30))
        cached_value = json.loads(raw_cached_value)
        return Hash.from_string(cached_value["blockhash"]), int(
            cached_value["last_valid_block_height"]
        )
