import asyncio

import aioredis
from aiogram import Bot
from aiogram.types import LinkPreviewOptions
from jinja2 import BaseLoader, Environment
from solbot_cache.token_info import TokenInfoCache
from solbot_common.cp.copytrade_event import NotifyCopyTradeConsumer
from solbot_common.log import logger
from solbot_common.types.swap import SwapEvent
from tg_bot.services.copytrade import CopyTradeService
from tg_bot.services.user import UserService
from tg_bot.utils.text import short_text

env = Environment(
    loader=BaseLoader(),
)
_BUY_TEMPLATE = env.from_string(
    """🎯 Copy Trade Trigger: Buy
🟢 {{wallet_name}} bought {{token_ui_amount}} ${{symbol}}

Wallet Address
<code>{{wallet_address}}</code>
Token Address
<code>{{mint}}</code>
<a href="https://solscan.io/tx/{{signature}}">View Transaction</a>
"""
)


_SELL_TEMPLATE = env.from_string(
    """🎯 Copy Trade Trigger: Sell
🔴 {{wallet_name}} sold {{token_ui_amount}} ${{symbol}}

Wallet Address
<code>{{wallet_address}}</code>
Token Address
<code>{{mint}}</code>
<a href="https://solscan.io/tx/{{signature}}">View Transaction</a>
"""
)


class CopyTradeNotify:
    """Copy Trade Notifications"""

    def __init__(
        self,
        redis: aioredis.Redis,
        bot: Bot,
        batch_size: int = 10,
        poll_timeout_ms: int = 5000,
    ):
        self.redis = redis
        self.bot = bot
        self.consumer = NotifyCopyTradeConsumer(
            redis_client=redis,
            consumer_group="copytrade_notify",
            consumer_name="copytrade_notify",
            batch_size=batch_size,
            poll_timeout_ms=poll_timeout_ms,
        )
        # Register the callback
        self.consumer.register_callback(self._handle_event)
        self.user_service = UserService()
        self.copytrade_service = CopyTradeService()
        self.token_info_cache = TokenInfoCache()

    async def _build_message(self, data: SwapEvent, chat_id: int) -> str:
        """Build message"""
        if data.by != "copytrade":
            raise ValueError("Invalid by")

        if data.tx_event is None:
            raise ValueError("tx_event is None")

        tx_event = data.tx_event
        if tx_event.tx_direction == "buy":
            template = _BUY_TEMPLATE
            sol_ui_amount = tx_event.to_amount / (10**tx_event.from_decimals)
            token_ui_amount = tx_event.from_amount / (10**tx_event.to_decimals)
        elif tx_event.tx_direction == "sell":
            template = _SELL_TEMPLATE
            token_ui_amount = tx_event.from_amount / (10**tx_event.from_decimals)
            sol_ui_amount = tx_event.to_amount / (10**tx_event.to_decimals)
        else:
            raise ValueError("Invalid by")

        token_info = await self.token_info_cache.get(tx_event.mint)
        if token_info is None:
            logger.warning(f"Failed to get token info: {tx_event.mint}")
            token_symbol = "Unknown"
        else:
            token_symbol = token_info.symbol

        wallet_alias = await self.copytrade_service.get_wallet_alias(
            target_wallet=tx_event.who,
            chat_id=chat_id,
        )

        return template.render(
            wallet_address=tx_event.who,
            wallet_name=wallet_alias if wallet_alias else short_text(tx_event.who),
            symbol=token_symbol,
            sol_ui_amount=sol_ui_amount,
            token_ui_amount=token_ui_amount,
            mint=tx_event.mint,
            signature=tx_event.signature,
        )

    async def _handle_event(self, data: SwapEvent):
        """Handle transaction event"""
        chat_ids = await self.user_service.get_chat_id_by_pubkey(data.user_pubkey)

        tasks = []
        for chat_id in chat_ids:
            message = await self._build_message(data, chat_id)
            tasks.append(
                self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML",
                    link_preview_options=LinkPreviewOptions(
                        is_disabled=True,
                    ),
                )
            )

        await asyncio.gather(*tasks)

    async def start(self):
        """Start copy trade notifications"""
        # Create task but don't wait for completion
        consumer_task = asyncio.create_task(self.consumer.start())
        # Add task completion callback to handle potential exceptions
        consumer_task.add_done_callback(lambda t: t.exception() if t.exception() else None)

    def stop(self):
        """Stop copy trade notifications"""
        self.consumer.stop()
