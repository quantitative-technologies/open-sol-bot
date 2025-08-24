import asyncio
import signal

from cache_preloader.services.auto_update_service import AutoUpdateCacheService
from solbot_common.log import logger
from solbot_common.prestart import pre_start


async def main():
    """Main function"""
   
    pre_start()

    service = AutoUpdateCacheService()

    def signal_handler():
        """Signal processing function"""
        logger.info("Received shutdown signal")
        # Use create_task to avoid blocking signal handling
        stop_task = asyncio.create_task(service.stop())
        # Add task completion callback to handle potential exceptions
        stop_task.add_done_callback(lambda t: t.exception() if t.exception() else None)

    # Register signal handlers
    loop = asyncio.get_running_loop()

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        # Start service and wait for completion
        await service.start()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        # Remove signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.remove_signal_handler(sig)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
