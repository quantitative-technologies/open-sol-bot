"""Tests for the trading route finding logic"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from solana.rpc.async_api import AsyncClient
from solbot_common.constants import PUMP_FUN_PROGRAM, WSOL
from solbot_common.types.swap import SwapEvent
from solbot_common.types.tx import TxEvent, TxType
from solbot_common.utils.utils import get_async_client
from solders.pubkey import Pubkey
from trading.executor import TradingExecutor

from app.trading.trading.swap import SwapDirection
from app.trading.trading.transaction import TradingRoute

PUMP_FUN_PROGRAM_ID = str(PUMP_FUN_PROGRAM)
#RAY_V4_PROGRAM_ID = str(RAY_V4)

@pytest.fixture
def mock_rpc_client():
    return AsyncMock(spec=AsyncClient)

@pytest.fixture
def rpc_client():
    return get_async_client()

@pytest.fixture
def executor():
    return TradingExecutor(rpc_client)

# user_pubkey='GX9R7oSaaCWwithoJR3bNK2s77fkge9PFHwyMneBQ8pK' swap_mode='ExactIn
# ' input_mint='So11111111111111111111111111111111111111112' output_mint='4TXY5B4Gjh8HARzHNCnvbKQauXLmuFhnSS9TEPCa6472' amount=1000000 ui_amount=0.001 timestamp=1754797838 amount_pct=None swap_in_type
# ='qty' priority_fee=1e-05 slippage_bps=250 by='copytrade' dynamic_slippage=False min_slippage_bps=None max_slippage_bps=None program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P' tx_event=TxEvent
# (signature='3jYK6VgikQBuyb6jcvubS9tJJAWnZW4EzVGbsY7k4u6d8pTbMDQihhHtyGZ5VzSiD8E53EkuM153nWpFJzfSC6aG', from_amount=3012044281, from_decimals=9, to_amount=27322493985912, to_decimals=6, mint='4TXY5B4
# Gjh8HARzHNCnvbKQauXLmuFhnSS9TEPCa6472', who='8rvAsDKeAcEjEkiZMug9k8v1y8mW6gQQiMobd89Uy7qR', tx_type=<TxType.OPEN_POSITION: 'open_position'>, tx_direction='buy', timestamp=1754797838, pre_token_amoun
# t=0, post_token_amount=27322493985912, program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')

@pytest.fixture
def tx_event_from_logs():
    """Fixture that creates a TxEvent based on the actual log data"""
    return TxEvent(
        signature='3jYK6VgikQBuyb6jcvubS9tJJAWnZW4EzVGbsY7k4u6d8pTbMDQihhHtyGZ5VzSiD8E53EkuM153nWpFJzfSC6aG',
        from_amount=3012044281,
        from_decimals=9,
        to_amount=27322493985912,
        to_decimals=6,
        mint='4TXY5B4Gjh8HARzHNCnvbKQauXLmuFhnSS9TEPCa6472',
        who='8rvAsDKeAcEjEkiZMug9k8v1y8mW6gQQiMobd89Uy7qR',
        tx_type=TxType.OPEN_POSITION,
        tx_direction='buy',
        timestamp=1754797838,
        pre_token_amount=0,
        post_token_amount=27322493985912,
        program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
    )

@pytest.fixture
def swap_event_from_logs(tx_event_from_logs):
    """Fixture that creates a SwapEvent based on the actual log data"""
    return SwapEvent(
        user_pubkey='GX9R7oSaaCWwithoJR3bNK2s77fkge9PFHwyMneBQ8pK',
        swap_mode='ExactIn',
        input_mint='So11111111111111111111111111111111111111112',
        output_mint='4TXY5B4Gjh8HARzHNCnvbKQauXLmuFhnSS9TEPCa6472',
        amount=1000000,
        ui_amount=0.001,
        timestamp=1754797838,
        amount_pct=None,
        swap_in_type='qty',
        priority_fee=1e-05,
        slippage_bps=250,
        by='copytrade',
        dynamic_slippage=False,
        min_slippage_bps=None,
        max_slippage_bps=None,
        program_id='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
        tx_event=tx_event_from_logs
    )

# @pytest.fixture(params=[pytest.lazy_fixture('swap_event_from_logs')])
# def swap_event(request):
#     """Alias for swap_event_from_logs using pytest params"""
#     return request.param
@pytest.fixture
def swap_event(swap_event_from_logs):
    """Alias for swap_event_from_logs"""
    return swap_event_from_logs

@pytest.fixture(
    scope="module",
    params=[
        ('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8','6Q7GpNCtARwQSZtaWn3yuadPfteYzGxvP5Gqeswtpump'), 
        #(RAY_V4_PROGRAM_ID, "")
    ]  
)
def swap_event_old(request):
    param = request.param
    program_id, mint_address = param
    # Mock time.time()
    with patch('time.time', return_value=1234567890.0):
        current_time = time.time()  # Will return 1234567890.0

    return SwapEvent(
        user_pubkey=str(MagicMock(spec=Pubkey)),
        swap_mode='ExactIn',
        input_mint=str(WSOL),
        output_mint=mint_address,
        amount=1,
        ui_amount=1.0,
        timestamp=current_time,
        program_id=program_id,
        direction=SwapDirection.Buy
    )

@pytest.mark.asyncio
async def test_find_route(executor, swap_event):
    """Test the find_trading_route method"""
    route = await executor.find_route(swap_event)
    assert route == TradingRoute.PUMP
 