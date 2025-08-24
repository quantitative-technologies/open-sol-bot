"""
Message templates for Telegram bot responses using Jinja2
"""

from typing import TYPE_CHECKING

from jinja2 import BaseLoader, Environment
from solbot_common.models.token_info import TokenInfo
from solbot_common.types.bot_setting import BotSetting as Setting
from solbot_common.types.holding import HoldingToken
from solbot_common.utils.utils import keypair_to_private_key
from solders.keypair import Keypair  # type: ignore
from tg_bot.models.monitor import Monitor
from tg_bot.utils.bot import get_bot_name

if TYPE_CHECKING:
    from tg_bot.notify.smart_swap import SwapMessage

# Create Jinja2 environment
env = Environment(loader=BaseLoader())

# Define templates
START_TEMPLATE = env.from_string(
    """Hi {{ mention }}! 👋
💳 Wallet address:
<code>{{ wallet_address }}</code>
(Click to copy)

💰 Wallet balance: {{ balance }} SOL
{%- if expiration_datetime %}
⌚ Expiry time: {{ expiration_datetime }}
{%- endif %}
"""
)

# First use template (unregistered)
FIRST_USE_TEMPLATE = env.from_string(
    """Hi {{ mention }}! 👋

📝 Welcome to Solana Trading Bot!

💳 Wallet address:
<code>{{ wallet_address }}</code>
(Click to copy)

{%- if expiration_datetime %}
⌚ Expiry time: {{ expiration_datetime }}
{%- endif %}
Tips: Since this is your first time using the bot, a new wallet has been generated for you.
You can use the /wallet command at any time to change your wallet address or export your private key.
"""
)

COPYTRADE_TEMPLATE = env.from_string(
    """Copy Trade Settings:
Target wallet: <code>{{ target_wallet }}</code>
Copy ratio: {{ copy_ratio }}%
Maximum amount: {{ max_amount }} SOL
"""
)

COPYTRADE_MENU_TEMPLATE = env.from_string("""Currently {{ total }} copy trades, {{ active_cnt }} active""")

CREATE_COPYTRADE_MESSAGE = "📝 Create Copy Trade"
EDIT_COPYTRADE_MESSAGE = "📝 Edit Copy Trade"

# MONITOR
MONITOR_MENU_MESSAGE = """🔔 Monitor Settings\n
Monitor wallets you're interested in and receive real-time transaction notifications
"""

MONITOR_MENU_TEMPLATE = env.from_string(
    """🔔 Monitor Settings
Monitor wallets you're interested in and receive real-time transaction notifications

{% if monitors %}Current monitoring list:
{%- for monitor in monitors[:10] %}
{{ loop.index }}. {% if monitor.active %}🟢{% else %}🔴{% endif %} <code>{{ monitor.target_wallet }}</code>{% if monitor.wallet_alias %} - {{ monitor.wallet_alias }}{% endif %}
{%- endfor %}
{% endif %}"""
)

CREATE_MONITOR_MESSAGE = "📝 Create Monitor"
EDIT_MONITOR_MESSAGE = env.from_string(
    """📝 Edit Monitor

Target wallet: <code>{{ monitor.target_wallet }}</code>
Wallet alias: {{ monitor.wallet_alias }}
Status: {% if monitor.active %}🟢Monitoring{% else %}🔴Paused{% endif %}
"""
)


def render_monitor_menu(monitors: list[Monitor]):
    """Render monitoring menu message"""
    return MONITOR_MENU_TEMPLATE.render(monitors=monitors)


def render_edit_monitor_message(monitor: Monitor):
    return EDIT_MONITOR_MESSAGE.render(monitor=monitor)


# NOTIFY
NOTIFY_SWAP_TEMPLATE = env.from_string(
    """🔔 Transaction Notification\n
{{ human_description }}

📛 Wallet alias: {{ wallet_alias }} <code>{{ who }}</code>(Click to copy)
📝 Type: {{ tx_type_cn }}
💱 Transaction direction: {{ tx_direction }}
🪙 Token name: ${{ token_symbol }} ({{ token_name }})
🪙 Token address: <code>{{ mint }}</code>
💰 Transaction amount: {{ "%.4f"|format(from_amount) }} → {{ "%.4f"|format(to_amount) }}
📊 Position change: {{ position_change_formatted }}
💎 Current position: {{ "%.4f"|format(post_amount) }}
⏰ Time: {{ tx_time }}
🔗 Transaction details: <a href="https://solscan.io/tx/{{ signature }}">Solscan</a>
📊 K-line monitoring: <a href="https://gmgn.ai/sol/token/{{ mint }}">GMGN</a> | <a href="https://dexscreener.com/solana/{{ mint }}">DexScreen</a>
"""
)


def render_first_use_message(mention, wallet_address, expiration_datetime):
    return FIRST_USE_TEMPLATE.render(
        mention=mention,
        wallet_address=wallet_address,
        expiration_datetime=expiration_datetime,
    )


def render_start_message(mention, wallet_address, balance, expiration_datetime):
    """Render start message"""
    return START_TEMPLATE.render(
        mention=mention,
        wallet_address=wallet_address,
        balance=balance,
        expiration_datetime=expiration_datetime,
    )


def render_copytrade_message(target_wallet, copy_ratio, max_amount):
    """Render copy trade message"""
    return COPYTRADE_TEMPLATE.render(
        target_wallet=target_wallet,
        copy_ratio=copy_ratio,
        max_amount=max_amount,
    )


def render_copytrade_menu(total, active_cnt):
    """Render copy trade menu message"""
    return COPYTRADE_MENU_TEMPLATE.render(total=total, active_cnt=active_cnt)


def render_notify_swap(
    swap_message: "SwapMessage",
):
    """Render transaction notification message"""
    return NOTIFY_SWAP_TEMPLATE.render(
        human_description=swap_message.human_description,
        token_name=swap_message.token_name,
        token_symbol=swap_message.token_symbol,
        wallet_alias=swap_message.wallet_alias,
        tx_type_cn=swap_message.tx_type_cn,
        from_amount=swap_message.from_amount,
        to_amount=swap_message.to_amount,
        position_change_formatted=swap_message.position_change_formatted,
        post_amount=swap_message.post_amount,
        tx_time=swap_message.tx_time,
        signature=swap_message.signature,
        who=swap_message.target_wallet,
        mint=swap_message.mint,
        tx_direction=swap_message.tx_direction,
    )


SETTING_TEMPLATE = env.from_string(
    """Wallet address:
<code>{{ wallet_address }}</code> (Click to copy)

🚀️ Quick slip point: {{ quick_slippage }}
🛡️ Anti-slip points: {{ sandwich_slippage }}%
🟢 Buy priority fee:  {{ buy_priority_fee }} SOL
🔴 Selling priority fee:  {{ sell_priority_fee }} SOL

Automatic slip point: Automatically adjust the slip point according to the chart, range 2.5%~30%.
After turning on, it will only take effect in fast mode, and will not take effect in anti-clip mode.
"""
)


def render_setting_message(setting: Setting):
    wallet_address = setting.wallet_address
    sandwich_slippage = setting.get_sandwich_slippage_pct()
    buy_priority_fee = setting.buy_priority_fee
    sell_priority_fee = setting.sell_priority_fee
    if setting.auto_slippage:
        quick_slippage = "Automatic"
    else:
        quick_slippage = f"{setting.get_quick_slippage_pct()}%"

    return SETTING_TEMPLATE.render(
        wallet_address=wallet_address,
        quick_slippage=quick_slippage,
        sandwich_slippage=sandwich_slippage,
        buy_priority_fee=buy_priority_fee,
        sell_priority_fee=sell_priority_fee,
    )


SWAP_TOKEN_TEMPLATE = env.from_string(
    """{{ symbol }}({{ name }})
<code>{{ mint }}</code>
(Long press to copy)

Price ${{ price }}
📊 K-line monitoring: <a href="https://gmgn.ai/sol/token/{{ mint }}">GMGN</a> | <a href="https://dexscreener.com/solana/{{ mint }}">DexScreen</a>

💎 Position {{ holding_sol_balance }} SOL
| Token {{ holding_token_balance }}

⚙️ Buy {{ buy_priority_fee }} SOL | Sell {{ sell_priority_fee }} SOL (Click /set to modify)
"""
)


def render_swap_token_message(token_info: TokenInfo, setting: Setting):
    return SWAP_TOKEN_TEMPLATE.render(
        symbol=token_info.symbol,
        name=token_info.token_name,
        mint=token_info.mint,
        buy_priority_fee=setting.buy_priority_fee,
        sell_priority_fee=setting.sell_priority_fee,
    )


# 🔔 Security: Mint abandonment ✅ / Blacklist ✅ / Burning pool 100%✅
# ✅ Top 10 holders: 15.35%
# 🐀 Mouse hole: --
# ✅ Pool: $1.4M (2,804.72 SOL)
# 💊 Pump foreign market (29D)
# 🐦 Twitter | 🌏 Official website | ✈️ Telegram

# Price $0.04779     Market value $47.8M    K-line monitoring

# 💎 Position 1.041 SOL ($228.625)
# | Token 4,784.11 EVAN
# | Takeoff 3.41% 🚀
# | Average cost $0.04621 (Market value: $46.2M)
# | Total buy 1 SOL
# | Total sell 0 SOL
# 💳 Balance 0.72515 SOL

# ---------------------
# ⛽ Suggested priority fee tip: Quick 0.0029 SOL | Super quick 0.0038 SOL

BUY_SELL_TEMPLATE = env.from_string(
    """💡Trading Command Guide:

/buy: Buy tokens immediately
/sell: Sell tokens immediately
/create: Create buy/sell limit orders

Example commands:
/buy ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82 0.5
This means immediately buy 0.5 SOL worth of BOME tokens

/sell ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82 50
/sell ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82 50%
This means immediately sell 50% of your BOME token holdings
    """
)

WALLET_TEMPLATE = env.from_string(
    """🔑 Wallet address:
<code>{{ wallet }}</code> (Click to copy)

Wallet balance: {{ sol_balance }} SOL <a href="https://gmgn.ai/sol/address/{{ wallet }}">Transaction history</a>
WSOL balance: {{ wsol_balance }} WSOL
"""
)


def render_wallet_message(wallet: str, sol_balance: float, wsol_balance: float):
    return WALLET_TEMPLATE.render(
        wallet=wallet,
        sol_balance=sol_balance,
        wsol_balance=wsol_balance,
    )


NEW_WALLET_TEMPLATE = env.from_string(
    """🆕 Change to New Wallet
Change to a new wallet
⚠️ Currently only supports 1 wallet. After changing to a new wallet private key, the server will delete the old wallet private key and it cannot be recovered!
⚠️ After changing the wallet private key, all orders, wallet follows, CTO follows, and strategies on the original address will be automatically closed! Please handle assets manually
⚠️ Please backup your old wallet private key immediately (do not share with others)
Backup private key:
<code>{{ private_key }}</code> (Click to copy)

Tips: This message will be automatically deleted after 30 seconds
"""
)


def render_new_wallet_message(keypair: Keypair):
    private_key = keypair_to_private_key(keypair)
    return NEW_WALLET_TEMPLATE.render(private_key=private_key)


EXPORT_WALLET_TEMPLATE = env.from_string(
    """🔑 Wallet address:
<code>{{ wallet }}</code> (Click to copy)

🔐 Wallet private key:
<code>{{ private_key }}</code> (Click to copy)

⚠️ Do not share the private key with anyone (This message will be destroyed after 5 seconds)
"""
)


def render_export_wallet_message(keypair: Keypair):
    pubkey = keypair.pubkey().__str__()
    private_key = keypair_to_private_key(keypair)

    return EXPORT_WALLET_TEMPLATE.render(
        wallet=pubkey,
        private_key=private_key,
    )


ASSET_TEMPLATE = env.from_string(
    """🔑 Wallet address:
<code>{{ wallet }}</code> (Click to copy)

💰 Wallet balance: {{ sol_balance }} SOL

🔮 Token | Quantity
{%- for token in tokens %}
{{ loop.index }}. <a href="https://t.me/{{ bot_name }}?start=asset_{{ token.mint }}">{{ token.symbol }}</a> | {{ token.balance_str }}
{%- endfor -%}
"""
)


def render_asset_message(wallet: str, sol_balance: float, tokens: list[HoldingToken]):
    bot_name = get_bot_name()
    return ASSET_TEMPLATE.render(
        bot_name=bot_name,
        wallet=wallet,
        sol_balance=sol_balance,
        tokens=tokens,
    )
