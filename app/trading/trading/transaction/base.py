from abc import ABC, abstractmethod

from solana.rpc.async_api import AsyncClient
from solders.signature import Signature  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore


class TransactionSender(ABC):
    """Abstract base class for transaction sender"""

    def __init__(self, rpc_client: AsyncClient):
        self.rpc_client = rpc_client

    @abstractmethod
    async def send_transaction(
        self,
        transaction: VersionedTransaction,
        **kwargs,
    ) -> Signature:
        """Send transaction

        Args:
            transaction (VersionedTransaction): Transaction to send
            **kwargs: Optional keyword arguments

        Returns:
            Signature: Transaction signature
        """
        pass

    @abstractmethod
    async def simulate_transaction(
        self,
        transaction: VersionedTransaction,
    ) -> bool:
        """Simulate transaction

        Args:
            transaction (VersionedTransaction): Transaction to simulate

        Returns:
            bool: Whether simulation was successful
        """
        pass
