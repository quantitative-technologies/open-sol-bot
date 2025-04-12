from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tg_bot.models.monitor import Monitor


def monitor_keyboard_menu(
    monitor_items: list[Monitor] | None = None,
) -> InlineKeyboardMarkup:
    if monitor_items is None:
        monitor_items = []

    # Build monitor item button matrix
    items = []
    current_row = []

    for idx, item in enumerate(monitor_items[:10], 1):  # Limit to max 10 items
        if item.wallet_alias is None:
            assert item.target_wallet is not None
            wallet_name = item.target_wallet[:5] + "..."
        else:
            wallet_name = item.wallet_alias
        current_row.append(
            InlineKeyboardButton(
                text=f"{idx!s} - {wallet_name}",
                callback_data=f"monitor_{item.pk}",
            )
        )

        # New row after every 5 buttons or if it's the last item
        if len(current_row) == 5 or idx == len(monitor_items):
            items.append(current_row)
            current_row = []

    # Add the last row even if not full
    if current_row:
        items.append(current_row)

    # Stop all monitoring
    items.append(
        [
            InlineKeyboardButton(
                text="Stop All Monitoring",
                callback_data="stop_all_monitor",
            )
        ]
    )

    # Bottom buttons
    bottom_buttons = [
        InlineKeyboardButton(text="➕ Add New", callback_data="create_new_monitor"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_home"),
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            *items,  # 展开监听项目按钮矩阵
            bottom_buttons,  # 底部按钮
        ],
    )


def create_monitor_keyboard(monitor: Monitor) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter wallet address"
                        if monitor.target_wallet is None
                        else str(monitor.target_wallet)
                    ),
                    callback_data="set_address",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "Wallet alias (optional)"
                        if monitor.wallet_alias is None
                        else f"Wallet alias: {monitor.wallet_alias}"
                    ),
                    callback_data="set_wallet_alias",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_monitor",
                ),
                InlineKeyboardButton(
                    text="✅ Confirm",
                    callback_data="submit_monitor",
                ),
            ],
        ]
    )


def edit_monitor_keyboard(monitor: Monitor) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "Please enter wallet address"
                        if monitor.target_wallet is None
                        else str(monitor.target_wallet)
                    ),
                    callback_data="set_address",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        "Wallet alias (optional)"
                        if monitor.wallet_alias is None
                        else f"Wallet alias: {monitor.wallet_alias}"
                    ),
                    callback_data="set_wallet_alias",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Delete Monitor",
                    callback_data="delete_monitor",
                ),
                InlineKeyboardButton(
                    text="Stop Monitor" if monitor.active else "Start Monitor",
                    callback_data="toggle_monitor",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_monitor",
                ),
            ],
        ]
    )
