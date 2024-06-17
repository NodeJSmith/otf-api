import functools
import inspect
import traceback
from collections.abc import Awaitable, Callable
from typing import Any, NoReturn, ParamSpec, TypeGuard, TypeVar

import typer
from click.exceptions import ClickException

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


def exit_with_error(message: Any, code: int = 1, **kwargs: Any) -> NoReturn:
    """
    Utility to print a stylized error message and exit with a non-zero code
    """
    from otf_api.cli.app import base_app

    kwargs.setdefault("style", "red")
    base_app.console.print(message, **kwargs)
    raise typer.Exit(code)


def exit_with_success(message: Any, **kwargs: Any) -> NoReturn:
    """
    Utility to print a stylized success message and exit with a zero code
    """
    from otf_api.cli.app import base_app

    kwargs.setdefault("style", "green")
    base_app.console.print(message, **kwargs)
    raise typer.Exit(0)


def with_cli_exception_handling(fn: Callable[[Any], Any]) -> Callable[[Any], Any]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any | None:
        try:
            return fn(*args, **kwargs)
        except (typer.Exit, typer.Abort, ClickException):
            raise  # Do not capture click or typer exceptions
        except Exception:
            traceback.print_exc()
            exit_with_error("An exception occurred.")

    return wrapper
