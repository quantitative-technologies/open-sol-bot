import asyncio

import aioredis
from aiogram import Bot

from .copytrade_trigger import CopyTradeNotify
from .smart_swap import SmartWalletSwapAlertNotify
from .swap_result import SwapResultNotify


class Notify:
    """Notification Manager"""
    def __init__(self, redis: aioredis.Redis, bot: Bot):
        self.smart_wallet_swap_notify = SmartWalletSwapAlertNotify(redis, bot)
        self.swap_result_notify = SwapResultNotify(redis, bot)
        self.copytrade_notify = CopyTradeNotify(redis, bot)

    async def start(self):
        """Start all notification services"""
        tasks = [
            self.smart_wallet_swap_notify.start(),
            self.swap_result_notify.start(),
            self.copytrade_notify.start(),
        ]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop all notification services"""
        self.smart_wallet_swap_notify.stop()
        self.swap_result_notify.stop()
        self.copytrade_notify.stop()
