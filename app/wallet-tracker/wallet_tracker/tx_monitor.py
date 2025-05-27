from collections.abc import Sequence
from typing import Literal

from solbot_common.config import settings
from solbot_common.cp.monitor_events import (MonitorEvent,
                                             MonitorEventConsumer,
                                             MonitorEventType)
from solbot_common.log import logger
from solbot_common.models.tg_bot.monitor import Monitor
from solbot_db.redis import RedisClient
from solbot_services.copytrade import CopyTradeService
from solders.pubkey import Pubkey  # type: ignore

from .geyser.tx_subscriber import TransactionDetailSubscriber as GeyserMonitor
from .wss.tx_subscriber import TransactionDetailSubscriber as RPCMonitor


class TxMonitor:
    def __init__(
        self,
        wallets: Sequence[Pubkey],
        mode: Literal["wss", "geyser"] = "wss",
    ):
        self.mode = mode
        redis = RedisClient.get_instance()
        self.events = MonitorEventConsumer(redis)
        if mode == "wss":
            self.monitor = RPCMonitor(
                settings.rpc.rpc_url,
                redis,
                wallets,
            )
        elif mode == "geyser":
            self.monitor = GeyserMonitor(
                settings.rpc.geyser.endpoint,
                settings.rpc.geyser.api_key,
                redis,
                wallets,
            )
        else:
            raise ValueError("Invalid mode")

    async def start(self):
        """Start the monitor"""
        # Register event handlers
        self.events.register_handler(MonitorEventType.RESUME, self._handle_resume_event)
        self.events.register_handler(MonitorEventType.PAUSE, self._handle_pause_event)

        # Subscribe to events
        pubsub = await self.events.subscribe()
        logger.info("Transaction monitor started")
        logger.info(f"Mode: {self.mode}")

        # Start the monitor
        await self.monitor.start()

        # Get active target addresses from database
        monitor_addresses = await Monitor.get_active_wallet_addresses()
        copytrade_addresses = await CopyTradeService.get_active_wallet_addresses()
        # Merge the two lists
        active_wallet_addresses = list(set(list(monitor_addresses) + list(copytrade_addresses)))
        for address in active_wallet_addresses:
            await self.monitor.subscribe_wallet_transactions(Pubkey.from_string(address))
            logger.debug(f"Subscribed to wallet: {address}")

        # Start processing events
        logger.info("Start processing monitor events")
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                if message is None:
                    continue
                await self.events.process_event(message)
            except Exception as e:
                logger.error(f"Error processing monitor event: {e}")

    async def stop(self):
        """Stop the monitor"""
        await self.events.unsubscribe()
        await self.monitor.stop()

    async def _handle_resume_event(self, event: MonitorEvent):
        """Handle resume monitoring event"""
        try:
            wallet = Pubkey.from_string(event.target_wallet)
            await self.monitor.subscribe_wallet_transactions(wallet)
            logger.info(f"Resumed monitoring wallet: {wallet}")
        except Exception as e:
            logger.error(f"Failed to resume monitoring wallet {event.target_wallet}: {e}")
            raise

    async def _handle_pause_event(self, event: MonitorEvent):
        """Handle pause monitoring event"""
        try:
            wallet = Pubkey.from_string(event.target_wallet)
            await self.monitor.unsubscribe_wallet_transactions(wallet)
            logger.info(f"Paused monitoring wallet: {wallet}")
        except Exception as e:
            logger.error(f"Failed to pause monitoring wallet {event.target_wallet}: {e}")
            raise
