import asyncio

from cache_preloader.caches.blockhash import BlockhashCache
from cache_preloader.caches.min_balance_rent import MinBalanceRentCache
from cache_preloader.core.protocols import AutoUpdateCacheProtocol
from solbot_common.log import logger
from solbot_db.redis import RedisClient


class AutoUpdateCacheService:
    """Automatically update cache service"""

    def __init__(self):
        self.redis_client = RedisClient.get_instance()
        self.auto_update_caches: list[AutoUpdateCacheProtocol] = [
            BlockhashCache(self.redis_client),
            MinBalanceRentCache(self.redis_client),
            # RaydiumPoolCache(settings.rpc.rpc_url, self.redis_client, 20),
        ]
        self._shutdown_event = asyncio.Event()
        self._main_task = None

    async def start(self):
        """Start cache service"""
        try:
            logger.info("Starting auto-update cache service...")
            # Start all cache services
            await asyncio.gather(*[cache.start() for cache in self.auto_update_caches])

            # Create a main monitoring task
            self._main_task = asyncio.create_task(self._monitor())
            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except asyncio.CancelledError:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.exception(f"Error in cache service: {e}")
        finally:
            await self.stop()

    async def _monitor(self):
        """Monitor the status of all cache services"""
        try:
            while not self._shutdown_event.is_set():
                # Check if all caches are running
                for cache in self.auto_update_caches:
                    if not cache.is_running():
                        logger.warning(f"{cache.__class__.__name__} is not running, restarting...")
                        await cache.start()
                # Check every minute
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Stop cache service"""
        logger.info("Stopping auto-update cache service...")

        # Set shutdown signal
        self._shutdown_event.set()

        # Cancel main monitoring task
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass

        # Stop all cache services
        await asyncio.gather(
            *[cache.stop() for cache in self.auto_update_caches], return_exceptions=True
        )

        # Record stop log
        for cache in self.auto_update_caches:
            logger.info(f"Stopped {cache.__class__.__name__}")
