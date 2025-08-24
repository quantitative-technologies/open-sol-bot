from aiogram import types
from aiogram.enums import ParseMode
from solbot_cache.wallet import WalletCache
from solbot_common.config import settings
from solbot_common.utils.shyft import ShyftAPI
from tg_bot.keyboards.wallet import get_wallet_keyboard
from tg_bot.services.user import UserService
from tg_bot.templates import render_wallet_message

shyft = ShyftAPI(settings.api.shyft_api_key)
user_service = UserService()
wallet_cache = WalletCache()


async def render(update: types.Message | types.CallbackQuery) -> dict:
    # Get user information
    if isinstance(update, types.CallbackQuery):
        # Get user information from callback query
        user = update.from_user
    else:
        # Get user information from message
        user = update.from_user

    if user is None:
        raise ValueError("User is None")

    wallet_address = await user_service.get_pubkey(user.id)
    balance = await wallet_cache.get_sol_balance(wallet_address)

    return {
        "text": render_wallet_message(
            wallet=wallet_address,
            sol_balance=balance,
            wsol_balance=0,
        ),
        "parse_mode": ParseMode.HTML,
        "reply_markup": get_wallet_keyboard(),
        "disable_web_page_preview": True,
    }
