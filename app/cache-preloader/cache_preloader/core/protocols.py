from typing import Protocol


class AutoUpdateCacheProtocol(Protocol):
    """Auto-update Cache Protocol"""

    def is_running(self) -> bool:
        """Check if cache service is running"""
        ...

    async def start(self):
        """Start cache service"""
        ...

    async def stop(self):
        """Stop cache service"""
        ...
