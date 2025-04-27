import asyncio

from solana.rpc.async_api import AsyncClient
from solbot_common.log import logger
from solders.keypair import Keypair  # type: ignore
from solders.signature import Signature  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from trading.swap import SwapDirection, SwapInType
from trading.transaction.base import TransactionSender
from trading.transaction.builders.base import TransactionBuilder
from trading.transaction.builders.gmgn import GMGNTransactionBuilder
from trading.transaction.builders.jupiter import JupiterTransactionBuilder
from trading.transaction.builders.pump import PumpTransactionBuilder
from trading.transaction.builders.ray_v4 import RaydiumV4TransactionBuilder
from trading.transaction.protocol import TradingRoute
from trading.transaction.sender import (DefaultTransactionSender,
                                        GMGNTransactionSender,
                                        JitoTransactionSender)


class Swapper:
    """Exchange service, coordinates the building and execution of swaps"""

    def __init__(self, builder: TransactionBuilder, sender: TransactionSender):
        """Initialize exchange service"""
        self.builder = builder
        self.sender = sender

    async def swap(
        self,
        keypair: Keypair,
        token_address: str,
        ui_amount: float,
        swap_direction: SwapDirection,
        slippage_bps: int,
        in_type: SwapInType | None = None,
        use_jito: bool = False,
        priority_fee: float | None = None,
    ) -> Signature | None:
        """Execute token swap operation

        Args:
            keypair (Keypair): Wallet keypair
            token_address (str): Token address
            ui_amount (float): Transaction amount
            swap_direction (SwapDirection): Swap direction
            slippage_bps (int): Slippage in bps
            in_type (SwapInType | None, optional): Input type. Defaults to None.
            use_jito (bool, optional): Whether to use Jito. Defaults to False.
            priority_fee (float | None, optional): Priority fee. Defaults to None.

        Returns:
            Optional[Signature]: Transaction signature, returns None if transaction fails
        """
        transaction = await self.builder.build_swap_transaction(
            keypair=keypair,
            token_address=token_address,
            ui_amount=ui_amount,
            swap_direction=swap_direction,
            slippage_bps=slippage_bps,
            in_type=in_type,
            use_jito=use_jito,
            priority_fee=priority_fee,
        )
        logger.debug(f"Built swap transaction: {transaction}")
        signature = await self.sender.send_transaction(transaction)
        logger.info(f"Transaction sent successfully: {signature}")
        return signature


class AggregateTransactionBuilder(TransactionBuilder):
    """Aggregates multiple transaction builders, returns the first successful result"""

    def __init__(self, rpc_client: AsyncClient, builders: list[TransactionBuilder]):
        """Initialize aggregate builder

        Args:
            rpc_client (AsyncClient): RPC client
            builders (List[TransactionBuilder]): List of transaction builders
        """
        super().__init__(rpc_client)
        self.builders = builders

    async def _try_build_with_builder(
        self,
        builder: TransactionBuilder,
        keypair: Keypair,
        token_address: str,
        ui_amount: float,
        swap_direction: SwapDirection,
        slippage_bps: int,
        in_type: SwapInType | None = None,
        use_jito: bool = False,
        priority_fee: float | None = None,
    ) -> tuple[TransactionBuilder, VersionedTransaction]:
        """Try to build transaction with specified builder

        Returns:
            Tuple[TransactionBuilder, VersionedTransaction]: Returns builder and built transaction
        """
        try:
            tx = await builder.build_swap_transaction(
                keypair=keypair,
                token_address=token_address,
                ui_amount=ui_amount,
                swap_direction=swap_direction,
                slippage_bps=slippage_bps,
                in_type=in_type,
                use_jito=use_jito,
                priority_fee=priority_fee,
            )
            return builder, tx
        except Exception as e:
            logger.warning(f"Builder {builder.__class__.__name__} failed: {e!s}")
            raise

    async def build_swap_transaction(
        self,
        keypair: Keypair,
        token_address: str,
        ui_amount: float,
        swap_direction: SwapDirection,
        slippage_bps: int,
        in_type: SwapInType | None = None,
        use_jito: bool = False,
        priority_fee: float | None = None,
    ) -> VersionedTransaction:
        """Try all builders in parallel, return the first successful transaction

        Raises:
            Exception: Raises exception when all builders fail

        Returns:
            VersionedTransaction: Built transaction
        """
        if not self.builders:
            raise ValueError("No transaction builders provided")

        # Create tasks for all builders
        tasks = [
            self._try_build_with_builder(
                builder,
                keypair,
                token_address,
                ui_amount,
                swap_direction,
                slippage_bps,
                in_type,
                use_jito,
                priority_fee,
            )
            for builder in self.builders
        ]

        # Wait for the first successful result
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                try:
                    builder, tx = await task
                    # Cancel other ongoing tasks
                    for p in pending:
                        p.cancel()
                    logger.info(f"Successfully built transaction with {builder.__class__.__name__}")
                    return tx
                except Exception:
                    # If this task failed, continue waiting for other tasks
                    pass

            # Update remaining tasks
            tasks = list(pending)

        raise Exception("All transaction builders failed")


class TradingService:
    """Trading service, coordinates the building and execution of trades"""

    def __init__(self, rpc_client: AsyncClient):
        """Initialize trading service"""
        self._rpc_client = rpc_client
        self._aggreage_txn_builder = AggregateTransactionBuilder(
            self._rpc_client,
            builders=[
                # GMGNTransactionBuilder(self._rpc_client),
                JupiterTransactionBuilder(self._rpc_client),
            ],
        )
        self._pump_txn_builder = PumpTransactionBuilder(self._rpc_client)
        self._raydium_v4_txn_builder = RaydiumV4TransactionBuilder(self._rpc_client)
        self._gmgn_sender = GMGNTransactionSender(self._rpc_client)
        self._jito_sender = JitoTransactionSender(self._rpc_client)
        self.default_sender = DefaultTransactionSender(rpc_client)

    def select_builder(self, route: TradingRoute) -> TransactionBuilder:
        if route == TradingRoute.PUMP:
            return self._pump_txn_builder
        elif route == TradingRoute.RAYDIUM_V4:
            return self._raydium_v4_txn_builder
        elif route == TradingRoute.DEX:
            return self._aggreage_txn_builder
        else:
            raise ValueError(f"Unsupported trading route: {route}")

    def select_sender(
        self, builder: TransactionBuilder, use_jito: bool = False
    ) -> TransactionSender:
        if isinstance(builder, GMGNTransactionBuilder):
            sender = self._gmgn_sender
        elif use_jito:
            sender = self._jito_sender
        else:
            sender = self.default_sender
        return sender

    def use_route(self, route: TradingRoute, use_jito: bool = False) -> Swapper:
        builder = self.select_builder(route)
        sender = self.select_sender(builder, use_jito)
        return Swapper(builder, sender)
