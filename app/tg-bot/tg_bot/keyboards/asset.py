from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_asset_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 return", callback_data="back_to_home"),
                InlineKeyboardButton(text="🔄 refresh", callback_data="asset:refresh"),
            ],
        ]
    )
    return keyboard
