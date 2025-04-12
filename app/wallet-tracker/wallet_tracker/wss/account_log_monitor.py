"""
Connect to RPC to monitor account logs
Monitor smart wallet transaction activities and push messages to Redis
"""

import asyncio
from collections.abc import Sequence

import aioredis
from _pickle import PicklingError
from solana.rpc.websocket_api import connect
from solbot_common.config import settings
from solbot_common.log import logger
from solders.errors import SerdeJSONError  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.rpc.config import RpcTransactionLogsFilterMentions  # type: ignore
from solders.rpc.responses import LogsNotification  # type: ignore
from solders.rpc.responses import SubscriptionResult
from wallet_tracker import benchmark
from wallet_tracker.constants import NEW_TX_SIGNATURE_CHANNEL
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


class AccountLogMonitor:
    def __init__(
        self,
        init_wallets: Sequence[Pubkey],
        rpc_endpoint: str,
        redis_client: aioredis.Redis,
        redis_channel: str = NEW_TX_SIGNATURE_CHANNEL,
    ):
        """
        Initialize the monitor

        Args:
            init_wallets: List of wallet addresses to monitor
            rpc_endpoint: Solana RPC endpoint
            redis_channel: Redis pub/sub channel name
        """
        self.init_wallets = list(init_wallets)
        self.websocket_url = rpc_endpoint.replace("https://", "wss://")
        self.redis_channel = redis_channel
        self.redis = redis_client
        self.is_running = False
        # FIXME: Currently using wallet-to-wallet mapping, need to consider if multiple wallets track the same target wallet.
        # If one wallet unsubscribes, could it prevent other wallets from receiving messages?
        self.subscription_ids = {}  # Store mapping between wallet addresses and subscription IDs
        self.websocket = None  # Store websocket connection
        self.waitting_subscribe_response_wallet = None  # Store wallet address waiting for subscription response
        self.subscribed_wallets = set()  # Store subscribed wallet addresses
        self.subscribe_lock = asyncio.Lock()  # Subscription lock
        self.waitting_subscribe_wallet: asyncio.Queue[Pubkey] = (
            asyncio.Queue()
        )  # Queue for wallets waiting to be subscribed
        self.waitting_unsubscribe_wallet: asyncio.Queue[Pubkey] = (
            asyncio.Queue()
        )  # Queue for wallets waiting to be unsubscribed
        self.__subscribe_task_join_handle = None  # Subscribe task handle
        self.__unsubscribe_task_join_handle = None  # Unsubscribe task handle

    async def process_log(self, message: LogsNotification) -> None:
        """
        Process received log data

        Args:
            message: Log data returned from WebSocket
        """
        try:
            signature = str(message.result.value.signature)
            assert self.redis is not None, "Redis is not connected"
            # Send to Redis
            await self.redis.lpush(self.redis_channel, signature)
            await benchmark.init(str(signature))
            logger.info(f"New tx signature: {signature}")
        except Exception as e:
            logger.error(f"Error processing log: {e}")

    async def process_subscribe_result(self, message: SubscriptionResult) -> None:
        subscription_id = message.result
        if self.waitting_subscribe_response_wallet is None:
            raise ValueError(f"Unexpected subscription result: {message}")

        async with self.subscribe_lock:
            self.subscription_ids[self.waitting_subscribe_response_wallet] = subscription_id
            old_wallet = self.waitting_subscribe_response_wallet
            self.waitting_subscribe_response_wallet = None

        logger.info(f"Subscribed to logs with subscription ID: {subscription_id}")
        if old_wallet not in self.subscribed_wallets:
            self.subscribed_wallets.add(old_wallet)

    async def subscribe_wallet(self, wallet: Pubkey) -> None:
        """Subscribe to a single wallet"""
        if not self.websocket:
            logger.warning(
                f"WebSocket connection is not established. Cannot subscribe to wallet: {wallet}"
            )
            return

        logger.debug(f"Subscribing to wallet: {wallet}")
        async with self.subscribe_lock:
            self.waitting_subscribe_response_wallet = str(wallet)
            await self.websocket.logs_subscribe(
                filter_=RpcTransactionLogsFilterMentions(wallet),
                commitment=settings.rpc.commitment,
            )

    async def unsubscribe_wallet(self, wallet: Pubkey) -> None:
        """Unsubscribe from a single wallet"""
        if not self.websocket:
            logger.warning(
                f"WebSocket connection is not established. Cannot subscribe to wallet: {wallet}"
            )
            return

        wallet_str = str(wallet)
        if wallet_str in self.subscription_ids:
            async with self.subscribe_lock:
                subscription_id = self.subscription_ids[wallet_str]
                del self.subscription_ids[wallet_str]
                self.subscribed_wallets.remove(wallet_str)
                await self.websocket.logs_unsubscribe(subscription_id)
            logger.info(f"Unsubscribed from wallet: {wallet}")

    async def __subscribe_task(self) -> None:
        """Subscribe to all wallets"""
        while self.is_running:
            try:
                wallet = await self.waitting_subscribe_wallet.get()
                await self.subscribe_wallet(wallet)
                self.waitting_subscribe_wallet.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in subscribe task: {e}")
        return

    async def __unsubscribe_task(self) -> None:
        """Unsubscribe from all wallets"""
        while self.is_running:
            try:
                wallet = await self.waitting_unsubscribe_wallet.get()
                await self.unsubscribe_wallet(wallet)
                self.waitting_unsubscribe_wallet.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in unsubscribe task: {e}")
        return

    async def start(self) -> None:
        """Start monitoring service"""
        self.is_running = True
        retry_count = 0
        max_retries = 5
        base_delay = 5

        while self.is_running:
            # When disconnected, need to resubscribe all previously subscribed wallets upon reconnection
            for wallet in self.subscribed_wallets:
                self.waitting_subscribe_wallet.put_nowait(Pubkey.from_string(wallet))

            try:
                async with connect(
                    self.websocket_url,
                    ping_timeout=30,
                    ping_interval=20,
                    close_timeout=20,
                ) as websocket:
                    self.websocket = websocket
                    logger.info(
                        f"Successfully connected to Solana WebSocket RPC({self.websocket_url})"
                    )
                    retry_count = 0  # Reset retry count on successful connection

                    for wallet in self.init_wallets:
                        await self.waitting_subscribe_wallet.put(wallet)

                    if self.__subscribe_task_join_handle is None:
                        self.__subscribe_task_join_handle = asyncio.create_task(
                            self.__subscribe_task()
                        )
                    if self.__unsubscribe_task_join_handle is None:
                        self.__unsubscribe_task_join_handle = asyncio.create_task(
                            self.__unsubscribe_task()
                        )

                    while self.is_running:
                        try:
                            messages = await websocket.recv()
                            for message in messages:
                                if isinstance(message, SubscriptionResult):
                                    await self.process_subscribe_result(message)
                                    continue
                                elif isinstance(message, LogsNotification):
                                    await self.process_log(message)
                        except (ConnectionClosedError, ConnectionClosedOK) as ws_error:
                            logger.warning(f"WebSocket connection closed: {ws_error}")
                            break
                        except (SerdeJSONError, PicklingError) as e:
                            # FIXME: Deserialization fails for messages received after unsubscribe
                            logger.warning(f"Skipping invalid message: {e}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            logger.exception(e)
                            break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                logger.exception(e)

            # Clean up and prepare for reconnection
            self.subscription_ids.clear()
            await self.cleanup()

            # Implement exponential backoff for all reconnection attempts
            retry_count += 1
            if retry_count > max_retries:
                logger.error(f"Maximum retries ({max_retries}) reached. Stopping monitor.")
                self.is_running = False
                break

            delay = min(base_delay * (2 ** (retry_count - 1)), 60)  # Cap at 60 seconds
            logger.info(
                f"Attempting reconnection in {delay} seconds (attempt {retry_count}/{max_retries})"
            )
            await asyncio.sleep(delay)

    async def cleanup(self) -> None:
        """Clean up connections"""
        try:
            if self.websocket:
                await self.websocket.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        try:
            if self.redis:
                await self.redis.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        if self.__subscribe_task_join_handle:
            self.__subscribe_task_join_handle.cancel()
            self.__subscribe_task_join_handle = None
        if self.__unsubscribe_task_join_handle:
            self.__unsubscribe_task_join_handle.cancel()
            self.__unsubscribe_task_join_handle = None

    async def stop(self) -> None:
        """Stop monitoring service"""
        self.is_running = False
        await self.cleanup()
        logger.info("Monitor stopped")
