from abc import ABC, abstractmethod

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from trading.swap import SwapDirection, SwapInType


class TransactionBuilder(ABC):
    """Abstract base class for transaction builder"""

    def __init__(self, rpc_client: AsyncClient):
        self.rpc_client = rpc_client

    @abstractmethod
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
        """Build transaction

        Args:
            keypair (Keypair): Wallet keypair
            token_address (str): Token address
            ui_amount (float): Transaction amount
            swap_direction (SwapDirection): Swap direction
            slippage_bps (int): Slippage in bps
            in_type (SwapInType | None, optional): Input type. Defaults to None.
            use_jito (bool, optional): Whether to use Jito. Defaults to False.
            priority_fee (Optional[float], optional): Priority fee. Defaults to None.

        Returns:
            VersionedTransaction: Built transaction
        """
        pass
