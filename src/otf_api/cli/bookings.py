from enum import Enum

import pendulum
import typer
from loguru import logger

import otf_api
from otf_api.cli.app import OPT_OUTPUT, AsyncTyper, OutputType, base_app
from otf_api.models.responses.bookings import BookingStatus

flipped_status = {item.value: item.name for item in BookingStatus}
FlippedEnum = Enum("CliBookingStatus", flipped_status)  # type: ignore


bookings_app = AsyncTyper(name="bookings", help="Get bookings data")
base_app.add_typer(bookings_app, aliases=["booking"])


def today() -> str:
    val: str = pendulum.yesterday().date().to_date_string()
    return val


def next_month() -> str:
    val: str = pendulum.now().add(months=1).date().to_date_string()
    return val


@bookings_app.command(aliases=["ls", "list"])
async def list_bookings(
    start_date: str = typer.Option(default_factory=today, help="Start date for bookings"),
    end_date: str = typer.Option(default_factory=next_month, help="End date for bookings"),
    status: FlippedEnum = typer.Option(None, case_sensitive=False, help="Booking status"),
    limit: int = typer.Option(None, help="Limit the number of bookings returned"),
    exclude_none: bool = typer.Option(
        True, "--exclude-none/--allow-none", help="Exclude fields with a value of None", show_default=True
    ),
    output: OutputType = OPT_OUTPUT,
) -> None:
    """
    List bookings data
    """

    logger.info("Listing bookings data")

    if output:
        base_app.output = output

    bk_status = BookingStatus.get_from_key_insensitive(status.value) if status else None

    if not base_app.api:
        base_app.api = await otf_api.Api.create(base_app.username, base_app.password)
    bookings = await base_app.api.member_api.get_bookings(start_date, end_date, bk_status, limit)

    kwargs = {"indent": 4, "exclude_none": exclude_none}

    if base_app.output == "json":
        base_app.print(bookings.model_dump_json(**kwargs))
    elif base_app.output == "table":
        base_app.print(bookings.to_table())


@bookings_app.command()
async def book(class_uuid: str) -> None:
    """
    Book a class
    """

    logger.info(f"Booking class {class_uuid}")

    if not base_app.api:
        base_app.api = await otf_api.Api.create(base_app.username, base_app.password)
    booking = await base_app.api.member_api.book_class(class_uuid)

    base_app.console.print(booking)


@bookings_app.command()
async def cancel(booking_uuid: str) -> None:
    """
    Cancel a booking
    """

    logger.info(f"Cancelling booking {booking_uuid}")

    if not base_app.api:
        base_app.api = await otf_api.Api.create(base_app.username, base_app.password)
    booking = await base_app.api.member_api.cancel_booking(booking_uuid)

    base_app.console.print(booking)
