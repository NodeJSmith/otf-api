import functools
import traceback
from collections.abc import Callable
from typing import Any, NoReturn

import typer
from click.exceptions import ClickException


def exit_with_error(message: Any, code: int = 1, **kwargs: Any) -> NoReturn:
    """
    Utility to print a stylized error message and exit with a non-zero code
    """
    from otf_api.cli.root import app

    kwargs.setdefault("style", "red")
    app.console.print(message, **kwargs)
    raise typer.Exit(code)


def exit_with_success(message: Any, **kwargs: Any) -> NoReturn:
    """
    Utility to print a stylized success message and exit with a zero code
    """
    from otf_api.cli.root import app

    kwargs.setdefault("style", "green")
    app.console.print(message, **kwargs)
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
