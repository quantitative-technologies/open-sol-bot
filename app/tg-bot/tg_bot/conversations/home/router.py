from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from solbot_common.log import logger
from tg_bot.conversations.states import StartStates
from tg_bot.services.activation import ActivationCodeService

from .render import render

router = Router()


@router.callback_query(F.data == "back_to_home")
async def back_to_home(callback: CallbackQuery):
    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    data = await render(callback)
    await callback.message.edit_text(**data)


@router.callback_query(F.data == "start:activation_code")
async def start_activation_code(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    await callback.message.edit_text(text="Please send activation code")
    await state.set_state(StartStates.WAITING_FOR_ACTIVATION_CODE)


@router.message(F.text, StartStates.WAITING_FOR_ACTIVATION_CODE)
async def handle_activation_code(message: Message, state: FSMContext):
    if message.text is None:
        logger.warning("No text found in message")
        return

    if message.from_user is None:
        logger.warning("No user found in message")
        return

    text = message.text.strip()
    activation_code_service = ActivationCodeService()
    is_activated = await activation_code_service.activate_user(message.from_user.id, text)
    if is_activated:
        expired_timestamp = await activation_code_service.get_user_expired_timestamp(
            message.from_user.id
        )  # seconds
        expired_datetime = datetime.fromtimestamp(expired_timestamp).strftime("%Y-%m-%d %H:%M:%S")
        await message.answer(
            f"✅ Activation successful! Valid until {expired_datetime}, please click /start to begin using the bot.",
        )
        await state.clear()
        logger.info(f"User {message.from_user.id} activate successfully")
    else:
        await message.answer(
            "❌ Activation code is invalid or expired, please try again or contact admin for a new code.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Enter activation code",
                            callback_data="start:activation_code",
                        )
                    ]
                ]
            ),
        )
        logger.info(f"User {message.from_user.id} activate failed")
