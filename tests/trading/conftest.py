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


#CopyTrade TxEvent
#TxEvent(signature='H6AkB4z1SW1iumzug8duP4cNY8B9ungRpVrfodLNq7eoSHd5WsJEiUdkvgZtPHJnozNQKoS73dkKKUWwqtKNHiz', from_amount=99999000000, from_decimals=6, to_amount=2119280, to_decimals=9, mint='7Rh9XrXpKRZYTBMtqRxKMXwH631jDWcCnWRP9o8Spump', who='8A2KcvmvGcaxGfamX5nS5CJtqyiiziBWTW96SV5WoSfF', tx_type=<TxType.REDUCE_POSITION: 'reduce_position'>, tx_direction='sell', timestamp=1757588000, pre_token_amount=4789987589459, post_token_amount=4689988589459, program_id=None)

@pytest.fixture
def tx_event_copytrade_from_logs() -> TxEvent:
    """CopyTrade TxEvent instance based on logged output."""
    return TxEvent(
        signature="H6AkB4z1SW1iumzug8duP4cNY8B9ungRpVrfodLNq7eoSHd5WsJEiUdkvgZtPHJnozNQKoS73dkKKUWwqtKNHiz",
        from_amount=99999000000,
        from_decimals=6,
        to_amount=2119280,
        to_decimals=9,
        mint="7Rh9XrXpKRZYTBMtqRxKMXwH631jDWcCnWRP9o8Spump",
        who="8A2KcvmvGcaxGfamX5nS5CJtqyiiziBWTW96SV5WoSfF",
        tx_type=TxType.REDUCE_POSITION,
        tx_direction="sell",
        timestamp=1757588000,
        pre_token_amount=4789987589459,
        post_token_amount=4689988589459,
        program_id=None,
    )

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


