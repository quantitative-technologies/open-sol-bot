"""Transaction Validator

Transaction validator is used to verify the on-chain status of transactions.
"""

import asyncio

from solbot_common.constants import SOL_DECIMAL
from solbot_common.log import logger
from solbot_common.models.swap_record import SwapRecord, TransactionStatus
from solbot_common.types.swap import SwapEvent
from solbot_common.utils.utils import validate_transaction
from solbot_db.session import NEW_ASYNC_SESSION, provide_session
from solders.signature import Signature  # type: ignore

from .analyzer import TransactionAnalyzer


class SwapSettlementProcessor:
    """Swap Transaction Settlement Processor

    Validates transaction results and writes to database
    """

    def __init__(self):
        self.analyzer = TransactionAnalyzer()

    @provide_session
    async def record(
        self,
        swap_event: SwapRecord,
        *,
        session=NEW_ASYNC_SESSION,
    ):
        """记录交易信息"""
        session.add(swap_event)
        await session.commit()

    async def validate(self, tx_hash: Signature) -> TransactionStatus | None:
        """Validates whether a transaction has been confirmed on-chain.

        Calling validate returns a coroutine that waits for the transaction's on-chain status for 60 seconds.
        If the coroutine times out, it returns None.

        Examples:
            >>> from solders.signature import Signature  # type: ignore
            >>> from solbot_common.models.swap_record import TransactionStatus
            >>> tx_hash = Signature.from_string("4uTy6e7h2SyxuwMyGsJ2Mxh3Rrj99CFeQ6uF1H8xFsEzW8xfrUZ9Xb8QxYutd5zt2cutP45CSPX3CypMAc3ykr2q")
            >>> status = await validator.validate(tx_hash)
            >>> if status == TransactionStatus.SUCCESS:
            ...     print("Transaction confirmed")
            ... elif status == TransactionStatus.FAILED:
            ...     print("Transaction failed")
            ... elif status == TransactionStatus.EXPIRED:
            ...     print("Transaction timed out")
            ... else:
            ...     print("Transaction status unknown")

        Args:
            tx_hash (Signature): Transaction hash

        Returns:
            Coroutine[None, None, TransactionStatus | None]: Coroutine
        """
        tx_status = None
        for _ in range(60):
            try:
                tx_status = await validate_transaction(tx_hash)
            except Exception as e:
                logger.error(f"Failed to get transaction status: {e}")
                await asyncio.sleep(1)
                continue

            if tx_status is True:
                return TransactionStatus.SUCCESS
            elif tx_status is False:
                return TransactionStatus.FAILED
            await asyncio.sleep(1)
        return TransactionStatus.EXPIRED

    async def process(self, signature: Signature | None, swap_event: SwapEvent) -> SwapRecord:
        """Process transaction

        Args:
            swap_event (SwapRecord): Transaction record
        """
        input_amount = swap_event.amount
        input_mint = swap_event.input_mint
        output_mint = swap_event.output_mint
        # PERF: Needs optimization, decimals should not be hardcoded
        if swap_event.swap_mode == "ExactIn":
            input_token_decimals = 9
            output_token_decimals = 6
        else:
            input_token_decimals = 6
            output_token_decimals = 9

        if signature is None:
            swap_record = SwapRecord(
                user_pubkey=swap_event.user_pubkey,
                swap_mode=swap_event.swap_mode,
                input_mint=swap_event.input_mint,
                output_mint=swap_event.output_mint,
                input_amount=swap_event.amount,
                input_token_decimals=input_token_decimals,
                output_amount=swap_event.amount,
                output_token_decimals=output_token_decimals,
            )
        else:
            tx_status = await self.validate(signature)
            if tx_status is None:
                swap_record = SwapRecord(
                    signature=str(signature),
                    status=TransactionStatus.EXPIRED,
                    user_pubkey=swap_event.user_pubkey,
                    swap_mode=swap_event.swap_mode,
                    input_mint=swap_event.input_mint,
                    output_mint=swap_event.output_mint,
                    input_amount=swap_event.amount,
                    input_token_decimals=input_token_decimals,
                    output_amount=swap_event.amount,
                    output_token_decimals=output_token_decimals,
                )
            else:
                data = await self.analyzer.analyze_transaction(
                    str(signature),
                    user_account=swap_event.user_pubkey,
                    mint=swap_event.output_mint,
                )
                logger.debug(f"Transaction analysis data: {data}")

                if swap_event.swap_mode == "ExactIn":
                    output_amount = int(abs(data["token_change"]) * 10**6)
                else:
                    output_amount = int(abs(data["swap_sol_change"]) * 10**9)

                swap_record = SwapRecord(
                    signature=str(signature),
                    status=tx_status,
                    user_pubkey=swap_event.user_pubkey,
                    swap_mode=swap_event.swap_mode,
                    input_mint=input_mint,
                    output_mint=output_mint,
                    input_amount=input_amount,
                    input_token_decimals=input_token_decimals,
                    output_amount=output_amount,
                    output_token_decimals=output_token_decimals,
                    program_id=swap_event.program_id,
                    timestamp=swap_event.timestamp,
                    fee=data["fee"],
                    slot=data["slot"],
                    sol_change=int(data["sol_change"] * SOL_DECIMAL),
                    swap_sol_change=int(data["swap_sol_change"] * SOL_DECIMAL),
                    other_sol_change=int(data["other_sol_change"] * SOL_DECIMAL),
                )

        swap_record_clone = swap_record.model_copy()
        await self.record(swap_record)
        return swap_record_clone
