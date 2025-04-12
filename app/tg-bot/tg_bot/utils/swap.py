from typing import TypedDict

from solbot_common.utils import get_associated_token_address, get_async_client
from solders.pubkey import Pubkey  # type: ignore
from spl.token.constants import TOKEN_2022_PROGRAM_ID  # type: ignore
from spl.token.constants import TOKEN_PROGRAM_ID


class TokenAccountBalance(TypedDict):
    amount: int
    decimals: int


async def get_token_account_balance(token_mint: str, owner: str) -> TokenAccountBalance | None:
    """Get token balance

    Args:
        token_mint (str): Token address
        owner (str): Owner address

    Returns:
        TokenAccountBalance | None: Balance in lamports, or None if not found
    """
    rpc_client = get_async_client()
    account = get_associated_token_address(
        Pubkey.from_string(owner), Pubkey.from_string(token_mint), TOKEN_PROGRAM_ID
    )
    resp = await rpc_client.get_token_account_balance(pubkey=account)
    try:
        value = resp.value
        return {
            "amount": int(value.amount),
            "decimals": value.decimals,
        }
    except AttributeError:
        pass

    account = get_associated_token_address(
        Pubkey.from_string(owner),
        Pubkey.from_string(token_mint),
        TOKEN_2022_PROGRAM_ID,
    )
    resp = await rpc_client.get_token_account_balance(pubkey=account)
    try:
        value = resp.value
    except AttributeError:
        return None
    return {
        "amount": int(value.amount),
        "decimals": value.decimals,
    }
