from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from solbot_common.types.bot_setting import BotSetting as Setting


def settings_keyboard(setting: Setting) -> InlineKeyboardMarkup:
    # Auto slippage button text
    auto_slippage_text = "✅ Auto Slippage On" if setting.auto_slippage else "❌ Auto Slippage Off"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=auto_slippage_text,
                    callback_data="setting:toggle_auto_slippage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        f"Quick Slippage {setting.get_quick_slippage_pct()}% ✏️"
                        if setting.auto_slippage
                        else f"✅ Quick Slippage {setting.get_quick_slippage_pct()}% ✏️"
                    ),
                    callback_data="setting:edit_quick_slippage",
                ),
                InlineKeyboardButton(
                    text=f"Anti-Sandwich Slippage {setting.get_sandwich_slippage_pct()}% ✏️",
                    callback_data="setting:edit_sandwich_slippage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Edit Buy Priority Fee",
                    callback_data="setting:edit_buy_priority_fee",
                ),
                InlineKeyboardButton(
                    text="Edit Sell Priority Fee",
                    callback_data="setting:edit_sell_priority_fee",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Auto Buy On" if setting.auto_buy else "❌ Auto Buy Off",
                    callback_data="setting:toggle_auto_buy",
                ),
                InlineKeyboardButton(
                    text="✅ Auto Sell On" if setting.auto_sell else "❌ Auto Sell Off",
                    callback_data="setting:toggle_auto_sell",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="----- Custom Buy -----",
                    callback_data="setting:custom_buy_divider",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{setting.custom_buy_amount_1} SOL ✏️",
                    callback_data="setting:edit_buy_amount_1",
                ),
                InlineKeyboardButton(
                    text=f"{setting.custom_buy_amount_2} SOL ✏️",
                    callback_data="setting:edit_buy_amount_2",
                ),
                InlineKeyboardButton(
                    text=f"{setting.custom_buy_amount_3} SOL ✏️",
                    callback_data="setting:edit_buy_amount_3",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{setting.custom_buy_amount_4} SOL ✏️",
                    callback_data="setting:edit_buy_amount_4",
                ),
                InlineKeyboardButton(
                    text=f"{setting.custom_buy_amount_5} SOL ✏️",
                    callback_data="setting:edit_buy_amount_5",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="----- Custom Sell -----",
                    callback_data="setting:custom_sell_divider",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{setting.custom_sell_amount_1 * 100}% ✏️",
                    callback_data="setting:edit_sell_amount_1",
                ),
                InlineKeyboardButton(
                    text=f"{setting.custom_sell_amount_2 * 100}% ✏️",
                    callback_data="setting:edit_sell_amount_2",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_home",
                )
            ],
        ]
    )
