"""Telegram bot decorators."""

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from aiogram.fsm.context import FSMContext

T = TypeVar("T", bound=Callable[..., Awaitable[Any]])


def clear_state(func: T) -> T:
    """
    Decorators：Clear after function execution is completed state。

    Note: The decorated function must have state: FSMContext parameter.

    usage:
    @clear_state
    async def handler(message: Message, state: FSMContext):
        ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Find it from the parameters FSMContext Example
        state = None
        for arg in args:
            if isinstance(arg, FSMContext):
                state = arg
                break
        if state is None:
            state = kwargs.get("state")

        if state is None:
            raise ValueError(
                f"Function {func.__name__} must have a state parameter of type FSMContext"
            )

        try:
            # Execute the original function
            result = await func(*args, **kwargs)
            # Clear state
            await state.clear()
            return result
        except Exception as e:
            # Clear the exception when it occurs state
            await state.clear()
            raise e

    return cast(T, wrapper)
