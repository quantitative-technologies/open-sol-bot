import random
import string
import time
from datetime import datetime

from solbot_common.models.tg_bot.activation_code import ActivationCode
from solbot_common.models.tg_bot.user_license import UserLicense
from solbot_db.session import NEW_ASYNC_SESSION, provide_session
from sqlmodel import select


class ActivationCodeService:
    @provide_session
    async def generate_code(self, seconds: int, *, session=NEW_ASYNC_SESSION) -> str:
        """
        Generate new activation code
        :param seconds: Valid duration in seconds after activation
        :return: Generated activation code
        """
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Check if code already exists
            result = await session.execute(
                select(ActivationCode).where(ActivationCode.code == code)
            )
            if result.first() is None:
                break

        activation_code = ActivationCode(code=code, valid_seconds=seconds)
        session.add(activation_code)
        return code

    # @provide_session
    # async def is_code_valid(
    #     self, code: str, *, session=NEW_ASYNC_SESSION
    # ) -> bool:
    #     """
    #     Check whether the activation code is valid
    #     :param activation_code: Activation code
    #     :return: Is it valid or not
    #     """
    #     result = await session.execute(
    #         select(ActivationCode).where(ActivationCode.code == code)
    #     )
    #     activation_code = result.scalar_one_or_none()
    #     if activation_code is None:
    #         return False

    @provide_session
    async def activate_user(self, chat_id: int, code: str, *, session=NEW_ASYNC_SESSION) -> bool:
        """
        Activate user
        :param chat_id: User's chat_id
        :param code: Activation code
        :return: Whether activation was successful
        """
        # Query activation code
        result = await session.execute(
            select(ActivationCode).where(ActivationCode.code == code, ActivationCode.used == False)
        )
        activation_code = result.scalar_one_or_none()
        if not activation_code:
            return False

        # Update activation code status
        activation_code.used = True
        activation_code.used_by = chat_id
        activation_code.used_at = datetime.now()

        # Update or create user license
        result = await session.execute(select(UserLicense).where(UserLicense.chat_id == chat_id))
        user_license = result.scalar_one_or_none()

        if user_license:
            user_license.expired_timestamp += activation_code.valid_seconds
        else:
            user_license = UserLicense(
                chat_id=chat_id,
                expired_timestamp=activation_code.valid_seconds + int(time.time()),
            )
            session.add(user_license)

        return True

    @provide_session
    async def get_user_license(
        self, chat_id: int, *, session=NEW_ASYNC_SESSION
    ) -> UserLicense | None:
        """
        Get user license information
        :param chat_id: User's chat_id
        :return: User license information
        """
        result = await session.execute(select(UserLicense).where(UserLicense.chat_id == chat_id))
        return result.scalar_one_or_none()

    @provide_session
    async def is_user_authorized(self, chat_id: int, *, session=NEW_ASYNC_SESSION) -> bool:
        """
        Check if user has available time
        :param chat_id: User's chat_id
        :return: Whether user has available time
        """
        user_license = await self.get_user_license(chat_id, session=session)
        return user_license is not None and user_license.expired_timestamp > int(time.time())

    @provide_session
    async def deduct_user_time(
        self, chat_id: int, seconds: int = 1, *, session=NEW_ASYNC_SESSION
    ) -> bool:
        """
        Deduct user's usage time
        :param chat_id: User's chat_id
        :param seconds: Number of seconds to deduct
        :return: Whether deduction was successful
        """
        result = await session.execute(select(UserLicense).where(UserLicense.chat_id == chat_id))
        user_license = result.scalar_one_or_none()

        if not user_license or user_license.expired_timestamp < seconds:
            return False

        user_license.expired_timestamp -= seconds
        return True

    @provide_session
    async def get_user_expired_timestamp(self, chat_id: int, *, session=NEW_ASYNC_SESSION) -> int:
        """Get expiration time (in seconds)
        :param chat_id: User's chat_id
        :return: User's expiration time (in seconds)
        """
        result = await session.execute(
            select(UserLicense.expired_timestamp).where(UserLicense.chat_id == chat_id)
        )
        return result.scalar_one_or_none() or 0
