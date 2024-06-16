from typing import cast

import pendulum
import typer
from loguru import logger

import otf_api
from otf_api.cli._types import AsyncTyper
from otf_api.cli.root import app
from otf_api.models.responses.enums import BookingStatus

bookings_app = AsyncTyper(name="bookings", help="Get bookings data")
app.add_typer(bookings_app, aliases=["booking"])

# TODO: figure out why mypy doesn't like these unless they are wrapped in cast


def today() -> str:
    val = pendulum.now().date().to_date_string()
    return cast(str, val)


def next_month() -> str:
    val = pendulum.now().add(months=1).date().to_date_string()
    return cast(str, val)


@bookings_app.command()
async def ls(
    start_date: str = typer.Option(default_factory=today),
    end_date: str = typer.Option(default_factory=next_month),
    status: BookingStatus = typer.Option(None),
) -> None:
    """
    List bookings data
    """
    logger.info("Listing bookings data")

    if not app.api:
        app.api = await otf_api.Api.create(app.username, app.password)
    bookings = await app.api.member_api.get_bookings(start_date, end_date, status)

    for booking in bookings:
        app.console.print(booking)
