from aiogram.enums import ParseMode
from solbot_cache.wallet import WalletCache
from solbot_services.holding import HoldingService
from tg_bot.keyboards.asset import get_asset_keyboard
from tg_bot.templates import render_asset_message

holding_service = HoldingService()
wallet_cache = WalletCache()


async def render(wallet: str):
    # PERF: Here we need to optimize it later, and it should be retrieved from the database instead of calling it Shyft API
    # During the program running, it is necessary to track the changes in the wallet's Token balance and update it to the database in a timely manner.    
    tokens = await holding_service.get_tokens(wallet, hidden_small_amount=True)
    sol_balance = await wallet_cache.get_sol_balance(wallet)

    text = render_asset_message(
        wallet=wallet,
        sol_balance=sol_balance,
        tokens=tokens,
    )

    return {
        "text": text,
        "parse_mode": ParseMode.HTML,
        "reply_markup": get_asset_keyboard(),
        "disable_web_page_preview": True,
    }
