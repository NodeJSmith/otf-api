import asyncio
import functools
import typing
from collections.abc import Callable

import typer
from rich.console import Console
from rich.theme import Theme

from otf_api.cli._utilities import with_cli_exception_handling
from otf_api.cli.asyncutils import is_async_fn

if typing.TYPE_CHECKING:
    from otf_api.api import Api


class AsyncTyper(typer.Typer):
    """
    Wraps commands created by `Typer` to support async functions and handle errors.
    """

    console: Console

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)

        self.console = Console(highlight=False, theme=Theme({"prompt.choices": "bold blue"}), color_system="auto")

        # TODO: clean these up later, just don't want warnings everywhere that these could be None
        self.api: Api = None  # type: ignore
        self.username: str = None  # type: ignore
        self.password: str = None  # type: ignore
        self.output: str = None  # type: ignore

    def add_typer(
        self,
        typer_instance: "AsyncTyper",
        *args: typing.Any,
        no_args_is_help: bool = True,
        aliases: list[str] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        """
        This will cause help to be default command for all sub apps unless specifically stated otherwise.
        """
        if aliases:
            for alias in aliases:
                super().add_typer(
                    typer_instance, *args, name=alias, no_args_is_help=no_args_is_help, hidden=True, **kwargs
                )

        return super().add_typer(typer_instance, *args, no_args_is_help=no_args_is_help, **kwargs)

    def command(
        self,
        name: str | None = None,
        *args: typing.Any,
        aliases: list[str] | None = None,
        **kwargs: typing.Any,
    ) -> Callable[[typing.Any], typing.Any]:
        """
        Create a new command. If aliases are provided, the same command function
        will be registered with multiple names.

        Provide `deprecated=True` to mark the command as deprecated. If `deprecated=True`,
        `deprecated_name` and `deprecated_start_date` must be provided.
        """

        def wrapper(fn: Callable[[typing.Any], typing.Any]) -> Callable[[typing.Any], typing.Any]:
            # click doesn't support async functions, so we wrap them in
            # asyncio.run(). This has the advantage of keeping the function in
            # the main thread, which means signal handling works for e.g. the
            # server and workers. However, it means that async CLI commands can
            # not directly call other async CLI commands (because asyncio.run()
            # can not be called nested). In that (rare) circumstance, refactor
            # the CLI command so its business logic can be invoked separately
            # from its entrypoint.
            if is_async_fn(fn):
                _fn = fn

                @functools.wraps(fn)
                def fn(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                    return asyncio.run(_fn(*args, **kwargs))  # type: ignore

                fn.aio = _fn  # type: ignore

            fn = with_cli_exception_handling(fn)

            # register fn with its original name
            command_decorator = super(AsyncTyper, self).command(name=name, *args, **kwargs)
            original_command = command_decorator(fn)

            # register fn for each alias, e.g. @marvin_app.command(aliases=["r"])
            if aliases:
                for alias in aliases:
                    super(AsyncTyper, self).command(
                        name=alias,
                        *args,
                        **{k: v for k, v in kwargs.items() if k != "aliases"},
                    )(fn)

            return typing.cast(Callable[[typing.Any], typing.Any], original_command)

        return wrapper

    def setup_console(self, soft_wrap: bool = True, prompt: bool = True) -> None:
        self.console = Console(
            highlight=False,
            color_system="auto",
            theme=Theme({"prompt.choices": "bold blue"}),
            soft_wrap=not soft_wrap,
            force_interactive=prompt,
        )
