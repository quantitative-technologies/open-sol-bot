import asyncio
from datetime import datetime, timedelta
from typing import Any

import aioredis
from cache_preloader.core.protocols import AutoUpdateCacheProtocol
from solbot_common.log import logger


class BaseAutoUpdateCache(AutoUpdateCacheProtocol):
    """Base class for all cache managers"""

    key: str
    update_interval: int = 30

    def __init__(self, redis: aioredis.Redis, update_interval: int = 30):
        """
        Args:
            redis: Redis client instance
            update_interval: Cache update interval (seconds)
        """
        self.redis = redis
        self._update_interval = update_interval
        self._last_update: datetime | None = None
        self._update_task: asyncio.Task | None = None
        self._is_running = False

    def is_running(self) -> bool:
        """Check if cache service is running"""
        return self._is_running

    async def start(self):
        """Start automatic update task"""
        if self._is_running:
            return
        self._is_running = True
        self._update_task = asyncio.create_task(self._auto_update())
        logger.info(f"{self.__class__.__name__} cache manager started")

    async def stop(self):
        """Stop automatic update task"""
        if not self._is_running:
            return
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
        logger.info(f"{self.__class__.__name__} cache manager stopped")

    async def _auto_update(self):
        """Automatic update task"""
        while self._is_running:
            try:
                val = await self._gen_new_value()
                await self.redis.set(self.key, val, ex=timedelta(seconds=self._update_interval))
                logger.info(f"Updated {self.__class__.__name__} cache, value: {val}")
                self._last_update = datetime.now()
                await asyncio.sleep(self._update_interval - 1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.__class__.__name__} error updating cache: {e}")
                await asyncio.sleep(1)  # Short delay before retry after error

    async def _gen_new_value(self) -> Any:
        """Generate new cache value"""
        raise NotImplementedError

    @property
    def last_update(self) -> datetime | None:
        """Get last update time"""
        return self._last_update

    def __del__(self):
        """Ensure update task is stopped when object is deleted"""
        if self._is_running:
            # TODO: Need to stop in a more elegant way
            return asyncio.create_task(self.stop())
