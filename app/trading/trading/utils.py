from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey  # type: ignore
from spl.token.instructions import get_associated_token_address


async def has_ata(client: AsyncClient, wallet: Pubkey, mint: Pubkey) -> bool:
    """This function checks if a wallet contains a specific token mint.

    Args:
      wallet (Pubkey): A public key representing a wallet address.
      mint (Pubkey): The `mint` parameter in the function `has_ata` is of type `Pubkey`. It is
        likely a public key representing a token mint in a blockchain or cryptocurrency context. Mints are
        responsible for creating new tokens and managing the token supply.
    """
    ata_address = get_associated_token_address(wallet, mint)
    resp = await client.get_account_info(ata_address)
    return bool(resp.value) if resp else False


def min_amount_with_slippage(input_amount: int, slippage_bps: int) -> int:
    return input_amount * (10000 - slippage_bps) // 10000


def max_amount_with_slippage(input_amount: int, slippage_bps: int) -> int:
    return input_amount * (10000 + slippage_bps) // 10000


def calc_tx_units(fee: float) -> tuple[int, int]:
    """Calculate unit price and unit limit based on desired priority fee

    Args:
        fee: Desired priority fee in SOL

    Returns:
        tuple[int, int]: (unit_price, unit_limit)
        - unit_price: Price per compute unit (in micro-lamports)
        - unit_limit: Maximum compute units for the transaction
    """
    # Set fixed compute unit limit
    unit_limit = 200_000

    # Convert SOL to lamports (1 SOL = 10^9 lamports)
    fee_in_lamports = int(fee * 1e9)

    # Calculate price per compute unit
    # Since unit_price is in micro-lamports, multiply by 1e6
    unit_price = int((fee_in_lamports * 1e6) / unit_limit)

    return unit_price, unit_limit


def calc_tx_units_and_split_fees(
    fee: float,
) -> tuple[int, int, float]:
    """Calculate unit price and unit limit based on desired priority fee, and calculate Jito tip

    Priority fee is 70%, Jito tip is 30%, see https://docs.jito.wtf/lowlatencytxnsend/#id19

    Args:
        fee (float): Total fee in SOL

    Returns:
        tuple[int, int, float]: (unit_price, unit_limit, jito_fee)
        - unit_price: Price per compute unit (in micro-lamports)
        - unit_limit: Maximum compute units for the transaction
        - jito_fee: Jito tip in SOL
    """
    priority_fee = fee * 0.7
    jito_fee = fee * 0.3
    unit_price, unit_limit = calc_tx_units(priority_fee)
    return unit_price, unit_limit, jito_fee
