from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from solbot_common.types.copytrade import CopyTrade, CopyTradeSummary
from tg_bot.utils import short_text


def copytrade_keyboard_menu(
    copytrade_items: list[CopyTradeSummary] | None = None,
) -> InlineKeyboardMarkup:
    if copytrade_items is None:
        copytrade_items = []

    items = []
    for item in copytrade_items:
        alias = item.wallet_alias
        if alias is not None:
            show_name = short_text(alias, max_length=10)
        else:
            show_name = short_text(item.target_wallet, max_length=10)

        items.append(
            [
                InlineKeyboardButton(
                    text="{} Copy Address: {}".format("🟢" if item.active else "🔴", show_name),
                    callback_data=f"copytrade_{item.pk}",
                )
            ]
        )

    if len(items) != 0:
        items.append(
            [
                InlineKeyboardButton(text="Stop All Copy Trading", callback_data="stop_all_copytrade"),
            ]
        )

    buttoms = [
        InlineKeyboardButton(text="➕ Create Copy Trade", callback_data="create_copytrade"),
        InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_copytrade"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_home"),
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            *items,
            buttoms,
        ]
    )


def create_copytrade_keyboard(udata: CopyTrade) -> InlineKeyboardMarkup:
    """Create keyboard for copytrade settings"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter copy trading address"
                        if udata.target_wallet is None
                        else str(udata.target_wallet)
                    ),
                    callback_data="set_address",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter wallet alias (optional)"
                        if udata.wallet_alias is None
                        else f"Wallet alias: {udata.wallet_alias}"
                    ),
                    callback_data="set_wallet_alias",
                )
            ],
            [
                InlineKeyboardButton(
                    text="{} Fixed Buy: {} SOL".format(
                        "✅" if udata.is_fixed_buy else "",
                        udata.fixed_buy_amount,
                    ),
                    callback_data="set_fixed_buy_amount",
                )
            ],
            [
                InlineKeyboardButton(
                    text="{} Auto Buy/Sell".format(
                        "✅" if udata.auto_follow else "",
                    ),
                    callback_data="toggle_auto_follow",
                ),
                InlineKeyboardButton(
                    text="{} Take Profit/Stop Loss".format(
                        "✅" if udata.stop_loss else "",
                    ),
                    callback_data="toggle_take_profile_and_stop_loss",
                ),
                InlineKeyboardButton(
                    text="{} Buy Only".format(
                        "✅" if udata.no_sell else "",
                    ),
                    callback_data="toggle_no_sell",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"Priority Fee: {udata.priority} SOL",
                    callback_data="set_priority",
                ),
                InlineKeyboardButton(
                    text="{} Anti-Sandwich: {}".format(
                        "✅" if udata.anti_sandwich else "❌",
                        "On" if udata.anti_sandwich else "Off",
                    ),
                    callback_data="toggle_anti_sandwich",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="{} Auto Slippage".format(
                        "✅" if udata.auto_slippage else "",
                    ),
                    callback_data="toggle_auto_slippage",
                ),
                InlineKeyboardButton(
                    text="{} Custom Slippage: {}%".format(
                        "✅" if udata.auto_slippage is False else "",
                        udata.custom_slippage,
                    ),
                    callback_data="set_custom_slippage",
                ),
            ],
            [
                InlineKeyboardButton(text="⬅️ Cancel", callback_data="back_to_copytrade"),
                InlineKeyboardButton(text="✅ Confirm Create", callback_data="submit_copytrade"),
            ],
        ],
    )


def edit_copytrade_keyboard(udata: CopyTrade) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter copy trading address"
                        if udata.target_wallet is None
                        else str(udata.target_wallet)
                    ),
                    callback_data="null",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter wallet alias (optional)"
                        if udata.wallet_alias is None
                        else f"Wallet alias: {udata.wallet_alias}"
                    ),
                    callback_data="set_wallet_alias",
                )
            ],
            [
                InlineKeyboardButton(
                    text="{} Fixed Buy: {} SOL".format(
                        "✅" if udata.is_fixed_buy else "",
                        udata.fixed_buy_amount,
                    ),
                    callback_data="set_fixed_buy_amount",
                )
            ],
            [
                InlineKeyboardButton(
                    text="{} Auto Sell".format(
                        "✅" if udata.auto_follow else "",
                    ),
                    callback_data="toggle_auto_follow",
                ),
                InlineKeyboardButton(
                    text="{} Take Profit/Stop Loss".format(
                        "✅" if udata.stop_loss else "",
                    ),
                    callback_data="toggle_take_profile_and_stop_loss",
                ),
                InlineKeyboardButton(
                    text="{} Buy Only".format(
                        "✅" if udata.no_sell else "",
                    ),
                    callback_data="toggle_no_sell",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"Priority Fee: {udata.priority} SOL",
                    callback_data="set_priority",
                ),
                InlineKeyboardButton(
                    text="{} Anti-Sandwich: {}".format(
                        "✅" if udata.anti_sandwich else "❌",
                        "On" if udata.anti_sandwich else "Off",
                    ),
                    callback_data="toggle_anti_sandwich",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="{} Auto Slippage".format(
                        "✅" if udata.auto_slippage else "",
                    ),
                    callback_data="toggle_auto_slippage",
                ),
                InlineKeyboardButton(
                    text="{} Custom Slippage: {}%".format(
                        "✅" if udata.auto_slippage is False else "",
                        udata.custom_slippage,
                    ),
                    callback_data="set_custom_slippage",
                ),
            ],
            [
                InlineKeyboardButton(text="Delete Copy Trade", callback_data="delete_copytrade"),
                InlineKeyboardButton(
                    text="Stop Copy Trade" if udata.active is True else "Start Copy Trade",
                    callback_data="toggle_copytrade",
                ),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_copytrade"),
            ],
        ],
    )


def take_profile_and_stop_loss_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Set Take Profit/Stop Loss", callback_data="set_tp_sl"),
            ],
            [
                InlineKeyboardButton(text="Move Take Profit/Stop Loss", callback_data="move_tp_sl"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_copytrade"),
                InlineKeyboardButton(text="✅ Confirm", callback_data="submit_copytrade"),
            ],
        ],
    )
