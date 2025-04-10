import asyncio
from typing import cast

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ForceReply, Message
from solbot_common.log import logger
from solbot_common.utils import keypair_to_private_key
from solbot_db.session import start_async_session
from solbot_services.bot_setting import BotSettingService as SettingService
from solders.keypair import Keypair  # type: ignore
from tg_bot.conversations.states import WalletStates
from tg_bot.keyboards.wallet import new_wallet_keyboard
from tg_bot.services.user import UserService
from tg_bot.templates import (render_export_wallet_message,
                              render_new_wallet_message)
from tg_bot.utils import delete_later
from tg_bot.utils.message import invalid_input_and_request_reinput
from tg_bot.utils.solana import validate_solana_private_key

router = Router()

user_service = UserService()


@router.callback_query(F.data == "wallet:refresh")
@router.callback_query(F.data == "wallet")
@router.callback_query(F.data == "wallet:back")
async def refresh(callback: CallbackQuery, state: FSMContext):
    from tg_bot.conversations.wallet.render import render

    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    data = await render(callback)
    try:
        await callback.message.edit_text(**data)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise e

    await state.set_state(WalletStates.MENU)


@router.callback_query(F.data == "wallet:new")
async def new_wallet(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    user_service = UserService()
    keypair = await user_service.get_keypair(chat_id=callback.from_user.id)
    text = render_new_wallet_message(keypair=keypair)
    keyboard = new_wallet_keyboard()
    await state.update_data(
        original_message_id=callback.message.message_id,
        original_chat_id=callback.message.chat.id,
    )
    await callback.message.edit_text(text=text, reply_markup=keyboard)
    await delete_later(callback.message, delay=30)


@router.callback_query(F.data == "wallet:import")
async def import_wallet(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    data = await state.get_data()
    original_message_id = cast(int, data.get("original_message_id"))
    original_chat_id = cast(str, data.get("original_chat_id"))
    if callback.message.bot is None:
        logger.warning("No bot found in message")
        return
    msg = await callback.message.answer("Please enter new wallet private key", reply_markup=ForceReply())
    await callback.message.bot.delete_message(
        chat_id=original_chat_id, message_id=original_message_id
    )
    await state.update_data(
        prompt_message_id=msg.message_id,
        prompt_chat_id=msg.chat.id,
    )
    await state.set_state(WalletStates.WAITING_FOR_NEW_PRIVATE_KEY)


@router.message(F.text, WalletStates.WAITING_FOR_NEW_PRIVATE_KEY)
async def handle_new_private_key(message: Message, state: FSMContext):
    if message.text is None:
        logger.warning("No text found in message")
        return

    new_private_key = message.text.strip()
    valid, error_message = validate_solana_private_key(new_private_key)
    if not valid:
        await invalid_input_and_request_reinput(
            text=error_message,
            last_message=message,
            state=state,
        )
        return

    if message.from_user is None:
        return

    try:
        user_service = UserService()
        async with start_async_session() as session:
            default_keypair = await user_service.get_keypair(
                chat_id=message.from_user.id, session=session
            )
            default_private_key = keypair_to_private_key(default_keypair)
            if default_private_key == new_private_key:
                await invalid_input_and_request_reinput(
                    text="⚠️ New wallet private key is the same as current default wallet, no update needed, please re-enter",
                    last_message=message,
                    state=state,
                )
                return

            # Delete message containing private key
            await message.delete()

            default_pubkey = default_keypair.pubkey().__str__()
            # NOTE: Delete previous default wallet, will support multiple wallets later
            # For multiple wallets, set this wallet as non-default and add additional validation for duplicate wallet imports
            await user_service.delete_wallet(
                chat_id=message.from_user.id,
                pubkey=default_pubkey,
                session=session,
            )
            new_keypair = Keypair.from_base58_string(new_private_key)
            await user_service.register(
                chat_id=message.from_user.id,
                keypair=new_keypair,
                is_default=True,
                session=session,
            )
            # Create default settings for this wallet
            await SettingService().create_default(
                chat_id=message.from_user.id,
                wallet_address=new_keypair.pubkey().__str__(),
            )
    except Exception as e:
        logger.exception(e)
        await message.answer("Failed to import new wallet private key, please try again")
        return

    data = await state.get_data()
    prompt_message_id = cast(int, data.get("prompt_message_id"))
    prompt_chat_id = cast(str, data.get("prompt_chat_id"))
    if message.bot is None:
        logger.warning("No bot found in message")
        return
    await message.bot.delete_message(chat_id=prompt_chat_id, message_id=prompt_message_id)

    await state.clear()
    await message.answer("Successfully imported new wallet private key")

    # Start main menu
    from tg_bot.conversations.home.command import start

    await start(message, state)


@router.callback_query(F.data == "wallet:export")
async def export(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        logger.warning("No message found in update")
        return

    if not isinstance(callback.message, Message):
        logger.warning("Message is not a Message object")
        return

    user_service = UserService()
    keypair = await user_service.get_keypair(chat_id=callback.from_user.id)
    text = render_export_wallet_message(keypair=keypair)
    msg = await callback.message.answer(text=text)
    await delete_later(msg, delay=5)
