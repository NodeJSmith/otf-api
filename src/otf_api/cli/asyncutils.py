import inspect
from collections.abc import Awaitable, Callable
from typing import TypeGuard, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")


def is_async_fn(func: Callable[P, R] | Callable[P, Awaitable[R]]) -> TypeGuard[Callable[P, Awaitable[R]]]:
    """
    Returns `True` if a function returns a coroutine.

    See https://github.com/microsoft/pyright/issues/2142 for an example use
    """
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    return inspect.iscoroutinefunction(func)
