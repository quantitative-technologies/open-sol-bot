import asyncio
import time

import backoff
import httpx
from solbot_common.cp.swap_event import SwapEventConsumer
from solbot_common.cp.swap_result import SwapResultProducer
from solbot_common.log import logger
from solbot_common.prestart import pre_start
from solbot_common.types.swap import SwapEvent, SwapResult
from solbot_common.utils.utils import get_async_client
from solbot_db.redis import RedisClient
from solders.signature import Signature  # type: ignore
from trading.copytrade import CopyTradeProcessor
from trading.executor import TradingExecutor
from trading.settlement import SwapSettlementProcessor


class Trading:
    def __init__(self):
        self.redis = RedisClient.get_instance()
        self.rpc_client = get_async_client()
        self.trading_executor = TradingExecutor(self.rpc_client)
        self.swap_settlement_processor = SwapSettlementProcessor()
        # Create multiple consumer instances
        self.num_consumers = 3  # Adjust number of consumers as needed
        self.swap_event_consumers = []
        for i in range(self.num_consumers):
            consumer = SwapEventConsumer(
                self.redis,
                "trading:swap_event",
                f"trading:new_swap_event:{i}",  # Create unique name for each consumer
            )
            consumer.register_callback(self._process_swap_event)
            self.swap_event_consumers.append(consumer)

        self.copytrade_processor = CopyTradeProcessor()

        self.swap_result_producer = SwapResultProducer(self.redis)
        # Add task pool and semaphore
        self.task_pool = set()
        self.max_concurrent_tasks = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

    async def _process_single_swap_event(self, swap_event: SwapEvent):
        """Process core logic for a single swap event"""
        async with self.semaphore:
            logger.info(f"Processing swap event: {swap_event}")

            try:
                sig = await self._execute_swap(swap_event)
                swap_result = await self._record_swap_result(sig, swap_event)
                logger.info(f"Successfully processed swap event: {swap_event}")
                return swap_result
            except (httpx.ConnectTimeout, httpx.ConnectError):
                logger.error("Connection error")
                await self._record_failed_swap(swap_event)
                return
            except Exception as e:
                logger.exception(f"Failed to process swap event: {swap_event}")
                # Record result even if an error occurs
                await self._record_failed_swap(swap_event)
                raise e

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectTimeout, httpx.ConnectError),
        max_tries=3,
        base=1.5,
        factor=0.1,
        max_time=2,
    )
    async def _execute_swap(self, swap_event: SwapEvent) -> Signature | None:
        """Execute transaction and return signature"""
        sig = await self.trading_executor.exec(swap_event)
        logger.info(f"Transaction submitted: {sig}")
        return sig

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectTimeout, httpx.ConnectError),
        max_tries=2,
        base=1.5,
        factor=0.1,
        max_time=2,
    )
    async def _record_swap_result(self, sig: Signature | None, swap_event: SwapEvent) -> SwapResult:
        """Record transaction result"""
        if not sig:
            return await self._record_failed_swap(swap_event)

        swap_record = await self.swap_settlement_processor.process(sig, swap_event)

        swap_result = SwapResult(
            swap_event=swap_event,
            swap_record=swap_record,
            user_pubkey=swap_event.user_pubkey,
            transaction_hash=str(sig),
            submmit_time=int(time.time()),
        )

        await self.swap_result_producer.produce(swap_result)
        logger.info(f"Recorded transaction: {sig}")
        return swap_result

    async def _record_failed_swap(self, swap_event: SwapEvent) -> SwapResult:
        """Record failed transaction result"""
        swap_result = SwapResult(
            swap_event=swap_event,
            user_pubkey=swap_event.user_pubkey,
            transaction_hash=None,
            submmit_time=int(time.time()),
        )
        await self.swap_result_producer.produce(swap_result)
        return swap_result

    async def _process_swap_event(self, swap_event: SwapEvent):
        """Create new task to process swap event"""
        task = asyncio.create_task(self._process_single_swap_event(swap_event))
        self.task_pool.add(task)
        task.add_done_callback(self.task_pool.discard)

    async def start(self):
        processor_task = asyncio.create_task(self.copytrade_processor.start())
        # Add task completion callback to handle potential exceptions
        processor_task.add_done_callback(lambda t: t.exception() if t.exception() else None)
        # Start all consumers
        for consumer in self.swap_event_consumers:
            await consumer.start()

    async def stop(self):
        """Gracefully stop all consumers"""
        # Stop copy trading
        self.copytrade_processor.stop()

        # Stop all consumers
        for consumer in self.swap_event_consumers:
            consumer.stop()

        if self.task_pool:
            logger.info("Waiting for remaining tasks to complete...")
            await asyncio.gather(*self.task_pool, return_exceptions=True)
        logger.info("All consumers stopped")


if __name__ == "__main__":
    pre_start()
    trading = Trading()
    try:
        asyncio.run(trading.start())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(trading.stop())
        logger.info("Shutdown complete")
