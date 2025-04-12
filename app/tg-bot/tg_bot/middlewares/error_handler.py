from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from loguru import logger


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Error in middleware: {e}")

            if (isinstance(event, Message) and event.text is not None) or (
                isinstance(event, CallbackQuery) and event.data is not None
            ):
                await event.answer("❌ Unknown error, please try again!If the problem persists, please contact the developer")
            else:
                logger.warning("Unknown event type")
                return
