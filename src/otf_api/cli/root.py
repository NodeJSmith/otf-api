import asyncio
import sys
from enum import Enum
from typing import cast

import typer

import otf_api
from otf_api.cli._types import AsyncTyper
from otf_api.cli._utilities import with_cli_exception_handling

app = AsyncTyper(add_completion=True, no_args_is_help=True)


class OutputType(str, Enum):
    json = "json"
    table = "table"


def version_callback(value: bool) -> None:
    if value:
        print(otf_api.__version__)
        raise typer.Exit()


def is_interactive() -> bool:
    return cast(bool, app.console.is_interactive)


@app.callback()  # type: ignore
@with_cli_exception_handling
def main(
    ctx: typer.Context,  # noqa
    version: bool = typer.Option(  # noqa
        None,
        "--version",
        "-v",
        # A callback is necessary for Typer to call this without looking for additional
        # commands and erroring when excluded
        callback=version_callback,
        help="Display the current version.",
        is_eager=True,
    ),
    prompt: bool = True,
    username: str = typer.Option(envvar=["OTF_EMAIL", "OTF_USERNAME"], help="Username for the OTF API"),
    password: str = typer.Option(envvar="OTF_PASSWORD", help="Password for the OTF API", hide_input=True),
    output: OutputType = typer.Option(
        "json", show_default=False, help="Output format - only json is supported currently"
    ),
) -> None:
    # Configure the output console after loading the profile
    app.setup_console(prompt=prompt)
    app.username = username
    app.password = password
    app.output = output

    # When running on Windows we need to ensure that the correct event loop policy is
    # in place or we will not be able to spawn subprocesses. Sometimes this policy is
    # changed by other libraries, but here in our CLI we should have ownership of the
    # process and be able to safely force it to be the correct policy.
    # https://github.com/PrefectHQ/prefect/issues/8206
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
