from solana.rpc.async_api import AsyncClient
from solbot_cache.token_info import TokenInfoCache
from solbot_common.constants import SOL_DECIMAL, WSOL
from solbot_common.utils.jupiter import JupiterAPI
from solders.keypair import Keypair  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from trading.swap import SwapDirection, SwapInType
from trading.tx import sign_transaction_from_raw

from .base import TransactionBuilder


class JupiterTransactionBuilder(TransactionBuilder):
    """Jupiter Transaction Builder"""

    def __init__(self, rpc_client: AsyncClient) -> None:
        super().__init__(rpc_client=rpc_client)
        self.token_info_cache = TokenInfoCache()
        self.jupiter_client = JupiterAPI()

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
        """Build swap transaction with GMGN API.

        Args:
            token_address (str): token address
            amount_in (float): amount in
            swap_direction (SwapDirection): swap direction
            slippage (int): slippage, percentage
            in_type (SwapInType | None, optional): in type. Defaults to None.
            use_jto (bool, optional): use jto. Defaults to False.
            priority_fee (float | None, optional): priority fee. Defaults to None.

        Returns:
            VersionedTransaction: The built transaction ready to be signed and sent
        """
        if swap_direction == "sell" and in_type is None:
            raise ValueError("in_type must be specified when selling")

        if swap_direction == SwapDirection.Buy:
            token_in = str(WSOL)
            token_out = token_address
            amount = int(ui_amount * SOL_DECIMAL)
        elif swap_direction == SwapDirection.Sell:
            token_info = await self.token_info_cache.get(token_address)
            if token_info is None:
                raise ValueError("Token info not found")
            decimals = token_info.decimals
            token_in = token_address
            token_out = str(WSOL)
            amount = int(ui_amount * 10**decimals)
        else:
            raise ValueError("swap_direction must be buy or sell")

        if use_jito and priority_fee is None:
            raise ValueError("priority_fee must be specified when using jito")

        swap_tx_response = await self.jupiter_client.get_swap_transaction(
            input_mint=token_in,
            output_mint=token_out,
            user_publickey=str(keypair.pubkey()),
            amount=amount,
            slippage_bps=slippage_bps,
            use_jito=use_jito,
            jito_tip_lamports=int(priority_fee * SOL_DECIMAL) if priority_fee else None,
        )
        swap_tx = swap_tx_response["swapTransaction"]
        signed_tx = await sign_transaction_from_raw(swap_tx, keypair)
        return signed_tx
