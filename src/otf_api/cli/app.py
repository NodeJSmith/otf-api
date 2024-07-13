import asyncio
import functools
import sys
import typing
from collections.abc import Callable
from enum import Enum

import typer
from loguru import logger
from rich.console import Console
from rich.theme import Theme

import otf_api
from otf_api.auth import OtfUser
from otf_api.cli._utilities import is_async_fn, with_cli_exception_handling

if typing.TYPE_CHECKING:
    from otf_api import Otf


class OutputType(str, Enum):
    json = "json"
    table = "table"
    interactive = "interactive"


def version_callback(value: bool) -> None:
    if value:
        print(otf_api.__version__)
        raise typer.Exit()


OPT_USERNAME: str = typer.Option(None, envvar=["OTF_EMAIL", "OTF_USERNAME"], help="Username for the OTF API")
OPT_PASSWORD: str = typer.Option(envvar="OTF_PASSWORD", help="Password for the OTF API", hide_input=True)
OPT_OUTPUT: OutputType = typer.Option(None, envvar="OTF_OUTPUT", show_default=False, help="Output format")
OPT_LOG_LEVEL: str = typer.Option("CRITICAL", help="Log level", envvar="OTF_LOG_LEVEL")
OPT_VERSION: bool = typer.Option(
    None, "--version", callback=version_callback, help="Display the current version.", is_eager=True
)


def register_main_callback(app: "AsyncTyper") -> None:
    @app.callback()  # type: ignore
    @with_cli_exception_handling
    def main_callback(
        ctx: typer.Context,  # noqa
        version: bool = OPT_VERSION,  # noqa
        username: str = OPT_USERNAME,
        password: str = OPT_PASSWORD,
        output: OutputType = OPT_OUTPUT,
        log_level: str = OPT_LOG_LEVEL,
    ) -> None:
        app.setup_console()
        app.set_username(username)
        app.password = password
        app.output = output or OutputType.table
        app.set_log_level(log_level)

        # When running on Windows we need to ensure that the correct event loop policy is
        # in place or we will not be able to spawn subprocesses. Sometimes this policy is
        # changed by other libraries, but here in our CLI we should have ownership of the
        # process and be able to safely force it to be the correct policy.
        # https://github.com/PrefectHQ/prefect/issues/8206
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class AsyncTyper(typer.Typer):
    """
    Wraps commands created by `Typer` to support async functions and handle errors.
    """

    console: Console

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)

        theme = Theme({"prompt.choices": "bold blue"})
        self.console = Console(highlight=False, theme=theme, color_system="auto")

        # TODO: clean these up later, just don't want warnings everywhere that these could be None
        self.api: Otf = None  # type: ignore
        self.username: str = None  # type: ignore
        self.password: str = None  # type: ignore
        self.output: OutputType = None  # type: ignore
        self.logger = logger
        self.log_level = "CRITICAL"

    def set_username(self, username: str | None = None) -> None:
        if username:
            self.username = username
            return

        if OtfUser.cache_file_exists():
            self.username = OtfUser.username_from_disk()
            return

        raise ValueError("Username not provided and not found in cache")

    def set_log_level(self, level: str) -> None:
        self.log_level = level
        logger.remove()
        logger.add(sys.stderr, level=self.log_level.upper())

    def print(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        if self.output == "json":
            self.console.print_json(*args, **kwargs)
        else:
            self.console.print(*args, **kwargs)

    def add_typer(
        self, typer_instance: "AsyncTyper", *args: typing.Any, aliases: list[str] | None = None, **kwargs: typing.Any
    ) -> typing.Any:
        aliases = aliases or []
        for alias in aliases:
            super().add_typer(typer_instance, *args, name=alias, no_args_is_help=True, hidden=True, **kwargs)

        return super().add_typer(typer_instance, *args, no_args_is_help=True, **kwargs)

    def command(
        self, name: str | None = None, *args: typing.Any, aliases: list[str] | None = None, **kwargs: typing.Any
    ) -> Callable[[typing.Any], typing.Any]:
        """
        Create a new command. If aliases are provided, the same command function
        will be registered with multiple names.
        """

        aliases = aliases or []

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


base_app = AsyncTyper(add_completion=True, no_args_is_help=True)
register_main_callback(base_app)
