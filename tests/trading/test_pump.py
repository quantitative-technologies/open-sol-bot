import os
from unittest.mock import AsyncMock, patch

import pytest
from solana.rpc.async_api import AsyncClient
#from trading.utils import get_async_client
from solbot_common.utils import get_async_client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from app.trading.trading.swap import SwapDirection
from app.trading.trading.transaction.builders.pump import \
    PumpTransactionBuilder

#from trading.swap import SwapDirection

#from trading.swap_protocols.pump import Pump

@pytest.fixture
def mock_rpc_client():
    """Mock RPC client for testing"""
    client = AsyncMock(spec=AsyncClient)
    return client

@pytest.fixture
def pump_builder():
    client = get_async_client()
    """Create a PumpTransactionBuilder instance with mocked client"""
    return PumpTransactionBuilder(client)

@pytest.mark.asyncio
@pytest.mark.skip(reason="Pump class seems to be removed")
async def test_swap_buy():
    client = get_async_client()

    keypair = Keypair.from_base58_string(os.environ["KEYPAIR"])
    pump = Pump(client)
    mint = "G1WcqfZxkZGHvPLRvbSpVDgzsWxuWxbi1GcufwcHpump"
    amount_in = 0.0001
    swap_direction = SwapDirection.Buy
    slippage = 1000
    sig = await pump.swap(keypair, mint, amount_in, swap_direction, slippage)
    print(sig)


# @pytest.mark.asyncio
# async def test_swap_sell_qty():
#     client = await get_async_client()

#     pump = Pump(client, settings.wallet.keypair)
#     mint = "HiPZWtXxEvgzKnMBfHGvZqHfvgaJ1YHZVhwai1Wd8t4J"
#     amount_in = 100000
#     swap_direction = "sell"
#     in_type = SwapInType.Qty
#     slippage = 10
#     sig = await pump.swap(mint, amount_in, swap_direction, slippage, in_type)
#     assert sig is not None


# @pytest.mark.asyncio
# async def test_swap_sell_pct():
#     client = get_async_client()

#     pump = Pump(client, settings.wallet.keypair)
#     mint = "HiPZWtXxEvgzKnMBfHGvZqHfvgaJ1YHZVhwai1Wd8t4J"
#     amount_in = 0.01  # 1%
#     swap_direction = "sell"
#     in_type = SwapInType.Pct
#     slippage = 10
#     sig = await pump.swap(mint, amount_in, swap_direction, slippage, in_type)
#     assert sig is not None
#     raise NotImplementedError

@pytest.mark.asyncio
@pytest.mark.parametrize("token_address", [
    "G1WcqfZxkZGHvPLRvbSpVDgzsWxuWxbi1GcufwcHpump",
    "7eLVcLZRg7ZuE8SXWqd4KE1zJ2XanWz9iR9YTKPrpump"
])
async def test_build_swap_transaction_buy(pump_builder, token_address):
    """Test building a buy swap transaction"""
    
    # Create test data
    keypair = Keypair()
    ui_amount = 0.0001
    swap_direction = SwapDirection.Buy
    slippage_bps = 1000

    # Build the transaction
    transaction = await pump_builder.build_swap_transaction(
        keypair=keypair,
        token_address=token_address,
        ui_amount=ui_amount,
        swap_direction=swap_direction,
        slippage_bps=slippage_bps
    )

    # Verify the result
    assert isinstance(transaction, VersionedTransaction)
    assert mock_rpc_client.get_account_info.called
