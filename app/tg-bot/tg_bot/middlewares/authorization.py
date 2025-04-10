from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from loguru import logger
from solbot_common.config import settings
from tg_bot.services.activation import ActivationCodeService


class AuthorizationMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if settings.tg_bot.mode != "private":
            return await handler(event, data)

        if event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id

        if settings.tg_bot.manager_id == user_id:
            return await handler(event, data)

        if event.from_user is None:
            logger.warning("No user found in message")
            return

        # If there is an activation code, verify if it is valid
        # If there is no activation code, ask user to input activation code
        if isinstance(event, Message) and event.text is not None:
            message = event
            text = event.text.strip()
            if text == "/chat_id" or text[0] != "/":
                return await handler(event, data)
        elif isinstance(event, CallbackQuery) and event.data is not None:
            message = event.message
            if event.data == "start:activation_code":
                return await handler(event, data)
        else:
            logger.warning("Unknown event type")
            return

        assert message is not None
        activation_code_service = ActivationCodeService()
        user_license = await activation_code_service.get_user_license(user_id)
        passed = False
        if user_license is None:
            await message.answer(
                "This is a private bot. Please enter activation code to continue.\nTo get an activation code, please contact the administrator.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Enter Activation Code",
                                callback_data="start:activation_code",
                            )
                        ]
                    ]
                ),
            )
        else:
            authorized = await activation_code_service.is_user_authorized(user_id)
            if authorized is False:
                await message.answer(
                    "❌ Invalid or expired activation code. Please try again or contact administrator for a new code.",
                )
            passed = True

        if passed:
            return await handler(event, data)
