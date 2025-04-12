from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_wallet_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="back_to_home"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="wallet:refresh"),
            ],
            [
                InlineKeyboardButton(text="🆕 Change Wallet", callback_data="wallet:new"),
                InlineKeyboardButton(text="🔐 Export Private Key", callback_data="wallet:export"),
            ],
        ]
    )
    return keyboard


def new_wallet_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Import private key", callback_data="wallet:import"),
                InlineKeyboardButton(text="🔙 return", callback_data="wallet:back"),
            ],
        ]
    )
    return keyboard
