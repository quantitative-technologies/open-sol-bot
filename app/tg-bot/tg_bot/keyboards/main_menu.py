from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="💸 Buy/Sell", callback_data="swap"),
            InlineKeyboardButton(text="👥 Copy Trade", callback_data="copytrade"),
        ],
        [
            InlineKeyboardButton(text="🔮 My Position", callback_data="asset"),
            InlineKeyboardButton(text="🔔 Trade Monitor", callback_data="monitor"),
        ],
        [
            InlineKeyboardButton(text="👛 Wallet Management", callback_data="wallet"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="set"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return reply_markup
