from types import SimpleNamespace

import pytest
from solbot_common.types.swap import SwapEvent
from solbot_common.types.tx import TxEvent, TxType
from solbot_common.utils import get_async_client


@pytest.fixture
async def rpc_client():
    """Real Async Solana RPC client shared across trading tests."""
    client = get_async_client()
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def executor(rpc_client):
    """Provide a TradingExecutor with external calls stubbed for determinism."""
    import app.trading.trading.executor as executor_module
    from app.trading.trading.executor import TradingExecutor

    trading_executor = TradingExecutor(rpc_client)

    return trading_executor

#SwapEvent:
#user_pubkey='5b9tuvErmHAXpfGNv4wyRDQx6mLhYp4tKry52gxhToBa' swap_mode='ExactIn' input_mint='So1111111111111111111111111111
#1111111111112' output_mint='8qAbzjWBxD2kxnNwE9voR9Xkr2zT8mg1aM6ri34Jpump' amount=50000000 ui_amount=0.05 timestamp=1756448961 amount_pct=None swap_in_type='qty' priority_fee=0.0001 slippage_bps=250 by='copytrade' dynamic_slippage=False min_sl
#ippage_bps=None max_slippage_bps=None program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P' tx_event=TxEvent(signature='53XTg3825Q46PVDeJ6qVoP7nHx3RxKwhNNarYGKgfbD8V4FTPyztxCXDsXU3pBPdcztn9PqgxfJg6cJgEBPZEQEB', from_amount=340004999, from_
#decimals=9, to_amount=4181819987502, to_decimals=6, mint='8qAbzjWBxD2kxnNwE9voR9Xkr2zT8mg1aM6ri34Jpump', who='DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj', tx_type=<TxType.ADD_POSITION: 'add_position'>, tx_direction='buy', timestamp=17564489
#61, pre_token_amount=25274744460671, post_token_amount=29456564448173, program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')


#SwapEvent #3
#user_pubkey='5b9tuvErmHAXpfGNv4wyRDQx6mLhYp4tKry52gxhToBa' swap_mode='ExactIn' input_mint='So11111111111111111111111111111111111111112' output_mint='7i
#CcjyC8NWooMmpjwaAuFPG7ZeGvSwDjKRMPcNdei3ve' amount=50000000 ui_amount=0.05 timestamp=1756687287 amount_pct=None swap_in_type='qty' priority_fee=0.0001 slippage_bps=250 by='copytrade' dynamic_slippage=False min_slippage_bps=None max_slippage_bps=None program_id='cpamdpZCGK
#Uy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG' tx_event=TxEvent(signature='4CL5kwExbe7JkFFjmGvTqdrpKhV8kjWkpZKy7ovR2GWU2dFBMJEXaBAfVBApzgAxNVKbSaNzuk7SZjnQbvwSyfZf', from_amount=5092044280, from_decimals=9, to_amount=8883051365766, to_decimals=6, mint='7iCcjyC8NWooMmpjwaAuFPG7ZeGvSwD
#jKRMPcNdei3ve', who='DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj', tx_type=<TxType.OPEN_POSITION: 'open_position'>, tx_direction='buy', timestamp=1756687287, pre_token_amount=0, post_token_amount=8883051365766, program_id='cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG')

@pytest.fixture
def tx_event_from_logs() -> TxEvent:
    """TxEvent instance based on logged output."""
    return TxEvent(
        signature="53XTg3825Q46PVDeJ6qVoP7nHx3RxKwhNNarYGKgfbD8V4FTPyztxCXDsXU3pBPdcztn9PqgxfJg6cJgEBPZEQEB",
        from_amount=340004999,
        from_decimals=9,
        to_amount=4181819987502,
        to_decimals=6,
        mint="8qAbzjWBxD2kxnNwE9voR9Xkr2zT8mg1aM6ri34Jpump",
        who="DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj",
        tx_type=TxType.ADD_POSITION,
        tx_direction="buy",
        timestamp=1756448961,
        pre_token_amount=25274744460671,
        post_token_amount=29456564448173,
        program_id="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
    )


@pytest.fixture
def swap_event_from_logs(tx_event_from_logs) -> SwapEvent:
    """Pump-style swap event resembling on-chain logs.

    Kept minimal to satisfy route selection.
    """
    return SwapEvent(
        user_pubkey="5b9tuvErmHAXpfGNv4wyRDQx6mLhYp4tKry52gxhToBa",
        swap_mode="ExactIn",
        input_mint="So11111111111111111111111111111111111111112",
        output_mint="8qAbzjWBxD2kxnNwE9voR9Xkr2zT8mg1aM6ri34Jpump",
        amount=50000000,
        ui_amount=0.05,
        timestamp=1756448961,
        amount_pct=None,
        swap_in_type="qty",
        priority_fee=0.0001,
        slippage_bps=250,
        by="copytrade",
        dynamic_slippage=False,
        min_slippage_bps=None,
        max_slippage_bps=None,
        program_id="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
        tx_event=tx_event_from_logs,
    )


@pytest.fixture
def swap_event_from_logs_second():
    """DEX-aggregator style event (no specific program id)."""
    return SimpleNamespace(
        swap_mode="ExactIn",
        input_mint="So11111111111111111111111111111111111111112",
        output_mint="G1WcqfZxkZGHvPLRvbSpVDgzsWxuWxbi1GcufwcHpump",
        program_id=None,
        user_pubkey="HyygEkpVJJpuUyUYdAWQTZMwX4Ee1BS9ND7Yd2YdkWQg",
        ui_amount=0.0001,
        slippage_bps=100,
        swap_in_type="Pct",
        priority_fee=None,
        amount=1000,
        timestamp=0,
    )


@pytest.fixture
def tx_event_from_logs_third() -> TxEvent:
    """Third TxEvent instance derived from logged example (#3)."""
    return TxEvent(
        signature="4CL5kwExbe7JkFFjmGvTqdrpKhV8kjWkpZKy7ovR2GWU2dFBMJEXaBAfVBApzgAxNVKbSaNzuk7SZjnQbvwSyfZf",
        from_amount=5092044280,
        from_decimals=9,
        to_amount=8883051365766,
        to_decimals=6,
        mint="7iCcjyC8NWooMmpjwaAuFPG7ZeGvSwDjKRMPcNdei3ve",
        who="DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj",
        tx_type=TxType.OPEN_POSITION,
        tx_direction="buy",
        timestamp=1756687287,
        pre_token_amount=0,
        post_token_amount=8883051365766,
        program_id="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
    )


@pytest.fixture
def swap_event_from_logs_third(tx_event_from_logs_third) -> SwapEvent:
    """Third SwapEvent matching the commented example (#3)."""
    return SwapEvent(
        user_pubkey="5b9tuvErmHAXpfGNv4wyRDQx6mLhYp4tKry52gxhToBa",
        swap_mode="ExactIn",
        input_mint="So11111111111111111111111111111111111111112",
        output_mint="7iCcjyC8NWooMmpjwaAuFPG7ZeGvSwDjKRMPcNdei3ve",
        amount=50000000,
        ui_amount=0.05,
        timestamp=1756687287,
        amount_pct=None,
        swap_in_type="qty",
        priority_fee=0.0001,
        slippage_bps=250,
        by="copytrade",
        dynamic_slippage=False,
        min_slippage_bps=None,
        max_slippage_bps=None,
        program_id="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
        tx_event=tx_event_from_logs_third,
    )

