import time

from aiogram.types import Message
from solbot_cache import TokenInfoCache
from solbot_common.constants import SOL_DECIMAL, WSOL
from solbot_common.cp.swap_event import SwapEventProducer
from solbot_common.log import logger
from solbot_common.types.swap import SwapEvent
from solbot_common.utils import calculate_auto_slippage
from solbot_db.redis import RedisClient
from solbot_services.bot_setting import BotSettingService as SettingService
from tg_bot.services.user import UserService
from tg_bot.templates import BUY_SELL_TEMPLATE
from tg_bot.utils.solana import validate_solana_address

from .render import render

setting_service = SettingService()
user_service = UserService()
token_info_cache = TokenInfoCache()


async def info_command(message: Message):
    """Send Token Address, reply with token trading interface"""
    logger.debug(message)
    if message.from_user is None:
        logger.warning("No message found in update")
        return

    if message.text is None:
        logger.warning("No text found in message")
        return

    text = message.text.strip()
    valid = validate_solana_address(text)
    if not valid:
        await message.answer(
            text="❌ Invalid Token Address, please re-enter:",
        )
        return

    token_info = await token_info_cache.get(text)
    if token_info is None:
        logger.info(f"❌ Could not find token information for {text}")
        return

    chat_id = message.from_user.id
    wallet = await user_service.get_pubkey(chat_id)
    setting = await setting_service.get(chat_id, wallet)

    if setting is None:
        raise ValueError("Setting not found")

    await message.answer(
        **render(
            token_info=token_info,
            setting=setting,
        ),
    )


async def swap_command(message: Message):
    if message.from_user is None:
        logger.warning("No message found in update")
        return

    if message.text is None:
        logger.warning("No text found in message")
        return

    text = message.text.strip()
    if text == "/buy" or text == "/sell":
        await message.answer(
            text=BUY_SELL_TEMPLATE.render(),
        )
        return

    try:
        cmd, token_mint, ui_amount = text.split()
    except ValueError:
        await message.answer(
            text="❌ Invalid input format, please re-enter:",
        )
        return

    cmd = cmd.replace("/", "")

    if cmd not in ["buy", "sell"]:
        await message.answer(
            text="❌ Invalid input format, please re-enter:",
        )
        return

    chat_id = message.from_user.id
    wallet = await user_service.get_pubkey(chat_id)
    setting = await setting_service.get(chat_id, wallet)
    if setting is None:
        raise ValueError("Setting not found")

    token_info = await token_info_cache.get(token_mint)
    if token_info is None:
        logger.info(f"No token info found for {token_mint}")
        await message.answer("❌ Unable to query token information")
        return

    if cmd == "buy":
        input_mint = WSOL.__str__()
        output_mint = token_info.mint
        from_amount = int(float(ui_amount) * SOL_DECIMAL)
        swap_mode = "ExactIn"
    else:
        if ui_amount.endswith("%"):
            await message.answer(
                text="Percentage-based selling is not supported yet",
            )
            return
        from_amount = int(float(ui_amount) * 10**token_info.decimals)
        input_mint = token_info.mint
        output_mint = WSOL.__str__()
        swap_mode = "ExactOut"

    if setting.sandwich_mode:
        slippage_bps = setting.sandwich_slippage_bps
    elif setting.auto_slippage:
        slippage_bps = await calculate_auto_slippage(
            input_mint=input_mint,
            output_mint=output_mint,
            amount=from_amount,
            swap_mode=swap_mode,
            min_slippage_bps=setting.min_slippage,
            max_slippage_bps=setting.max_slippage,
        )
    else:
        slippage_bps = setting.quick_slippage

    swap_event_producer = SwapEventProducer(RedisClient.get_instance())

    swap_event = SwapEvent(
        user_pubkey=wallet,
        swap_mode=swap_mode,
        input_mint=input_mint,
        output_mint=output_mint,
        amount=from_amount,
        ui_amount=from_amount,
        slippage_bps=slippage_bps,
        timestamp=int(time.time()),
        priority_fee=(setting.buy_priority_fee if cmd == "buy" else setting.sell_priority_fee),
    )
    if setting.auto_slippage:
        swap_event.dynamic_slippage = True
        swap_event.min_slippage_bps = setting.min_slippage
        swap_event.max_slippage_bps = setting.max_slippage

    await swap_event_producer.produce(swap_event=swap_event)

    if cmd == "buy":
        await message.answer(
            f"🚀 {token_info.symbol} Buy {ui_amount} SOL, Slippage: {slippage_bps / 100}%"
        )
        logger.info(
            f"Buy {ui_amount} SOL for {token_info.symbol}, slippage: {slippage_bps / 100} %"
        )
    else:
        await message.answer(f"🚀 Sell {ui_amount} {token_info.symbol}, Slippage: {slippage_bps / 100}%")
        logger.info(
            f"Sell {ui_amount} {token_info.symbol} for SOL, slippage: {slippage_bps / 100} %"
        )
