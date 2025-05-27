from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from solbot_common.types.bot_setting import BotSetting as Setting


def get_token_keyboard(setting: Setting, mint: str) -> InlineKeyboardMarkup:
    """Get token trading keyboard layout"""
    keyboard = []

    # First row: Market price, Orders, Refresh
    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Market Price" if True else "❌ Market Price",  # TODO: Only supports market price for now
                callback_data="toggle_price",
            ),
            # InlineKeyboardButton(text="Orders", callback_data="pending_orders"),
            InlineKeyboardButton(text="Refresh", callback_data=f"swap:refresh_{mint}"),
        ]
    )

    # Second row: Quick mode and Anti-sandwich mode
    keyboard.append(
        [
            InlineKeyboardButton(
                text=f"🚀 Quick Mode {'✅' if setting.auto_slippage else '❌'}",
                callback_data="toggle_quick_mode",
            ),
            InlineKeyboardButton(
                text=f"🛡️ Anti-Sandwich Mode {'✅' if setting.sandwich_mode else '❌'}",
                callback_data="toggle_sandwich_mode",
            ),
        ]
    )

    # Separator: Buy
    keyboard.append([InlineKeyboardButton(text="----- Buy -----", callback_data="separator_buy")])

    # Buy amount buttons (two rows)
    keyboard.append(
        [
            InlineKeyboardButton(
                text=f"🟢Buy {setting.custom_buy_amount_1} SOL",
                callback_data=f"buy_{setting.custom_buy_amount_1}_{mint}",
            ),
            InlineKeyboardButton(
                text=f"🟢Buy {setting.custom_buy_amount_2} SOL",
                callback_data=f"buy_{setting.custom_buy_amount_2}_{mint}",
            ),
            InlineKeyboardButton(
                text=f"🟢Buy {setting.custom_buy_amount_3} SOL",
                callback_data=f"buy_{setting.custom_buy_amount_3}_{mint}",
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=f"🟢Buy {setting.custom_buy_amount_4} SOL",
                callback_data=f"buy_{setting.custom_buy_amount_4}_{mint}",
            ),
            InlineKeyboardButton(
                text=f"🟢Buy {setting.custom_buy_amount_5} SOL",
                callback_data=f"buy_{setting.custom_buy_amount_5}_{mint}",
            ),
            InlineKeyboardButton(text="🟢Buy x SOL", callback_data=f"buyx_{mint}"),
        ]
    )

    # Separator: Sell
    keyboard.append([InlineKeyboardButton(text="----- Sell -----", callback_data="separator_sell")])

    # Sell percentage buttons
    keyboard.append(
        [
            InlineKeyboardButton(
                text=f"🔴Sell {setting.custom_sell_amount_1 * 100}%",
                callback_data=f"sell_{setting.custom_sell_amount_1 * 100}_{mint}",
            ),
            InlineKeyboardButton(
                text=f"🔴Sell {setting.custom_sell_amount_2 * 100}%",
                callback_data=f"sell_{setting.custom_sell_amount_2 * 100}_{mint}",
            ),
            InlineKeyboardButton(text="🔴Sell x%", callback_data=f"sell_custom_{mint}"),
        ]
    )

    # Break-even button
    # keyboard.append(
    #     [InlineKeyboardButton(text="🔴Break Even", callback_data="sell_breakeven")]
    # )

    # Bottom buttons: Back, Settings, Share trade screenshot
    keyboard.append(
        [
            InlineKeyboardButton(text="Back", callback_data="back_to_home"),
            InlineKeyboardButton(text="Settings", callback_data="set"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
