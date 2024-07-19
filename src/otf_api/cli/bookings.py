from enum import Enum

import pendulum
import typer
from loguru import logger

import otf_api
from otf_api.cli.app import OPT_OUTPUT, AsyncTyper, OutputType, base_app
from otf_api.cli.prompts import prompt_select_from_table
from otf_api.models.responses.bookings import BookingStatus
from otf_api.models.responses.classes import ClassType, ClassTypeCli, DoW

flipped_status = {item.value: item.name for item in BookingStatus}
FlippedEnum = Enum("CliBookingStatus", flipped_status)  # type: ignore


bookings_app = AsyncTyper(name="bookings", help="Get bookings data")
classes_app = AsyncTyper(name="classes", help="Get classes data")
base_app.add_typer(bookings_app, aliases=["booking"])
base_app.add_typer(classes_app, aliases=["class"])


def today() -> str:
    val: str = pendulum.yesterday().date().to_date_string()
    return val


def next_month() -> str:
    val: str = pendulum.now().add(months=1).date().to_date_string()
    return val


@bookings_app.command(name="list")
async def list_bookings(
    start_date: str = typer.Option(default_factory=today, help="Start date for bookings"),
    end_date: str = typer.Option(default_factory=next_month, help="End date for bookings"),
    status: FlippedEnum = typer.Option(None, case_sensitive=False, help="Booking status"),
    limit: int = typer.Option(None, help="Limit the number of bookings returned"),
    exclude_cancelled: bool = typer.Option(
        True, "--exclude-cancelled/--include-cancelled", help="Exclude cancelled bookings", show_default=True
    ),
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
        base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)
    bookings = await base_app.api.get_bookings(start_date, end_date, bk_status, limit, exclude_cancelled)

    if base_app.output == "json":
        base_app.print(bookings.to_json(exclude_none=exclude_none))
    elif base_app.output == "table":
        base_app.print(bookings.to_table())
    elif base_app.output == "interactive":
        result = prompt_select_from_table(
            console=base_app.console,
            prompt="Select a booking",
            columns=bookings.show_bookings_columns(),
            data=bookings.bookings,
        )
        print(result)


@bookings_app.command()
async def book(class_uuid: str = typer.Option(help="Class UUID to cancel")) -> None:
    """
    Book a class
    """

    logger.info(f"Booking class {class_uuid}")

    if not base_app.api:
        base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)
    booking = await base_app.api.book_class(class_uuid)

    base_app.console.print(booking)


@bookings_app.command()
async def book_interactive(
    studio_uuids: list[str] = typer.Option(None, help="Studio UUIDs to get classes for"),
    include_home_studio: bool = typer.Option(True, help="Include the home studio in the classes"),
    start_date: str = typer.Option(default_factory=today, help="Start date for classes"),
    end_date: str = typer.Option(None, help="End date for classes"),
    limit: int = typer.Option(None, help="Limit the number of classes returned"),
    class_type: list[ClassTypeCli] = typer.Option(None, help="Class type to filter by"),
    day_of_week: list[DoW] = typer.Option(None, help="Days of the week to filter by"),
    exclude_cancelled: bool = typer.Option(
        True, "--exclude-cancelled/--allow-cancelled", help="Exclude cancelled classes", show_default=True
    ),
    start_time: list[str] = typer.Option(None, help="Start time for classes"),
) -> None:
    """
    Book a class interactively
    """

    logger.info("Booking class interactively")

    with base_app.console.status("Getting classes...", spinner="arc"):
        if class_type:
            class_type_enums = [ClassType.get_from_key_insensitive(class_type.value) for class_type in class_type]
        else:
            class_type_enums = None

        if not base_app.api:
            base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)

        classes = await base_app.api.get_classes(
            studio_uuids,
            include_home_studio,
            start_date,
            end_date,
            limit,
            class_type_enums,
            exclude_cancelled,
            day_of_week,
            start_time,
        )

    result = prompt_select_from_table(
        console=base_app.console,
        prompt="Book a class, any class",
        columns=classes.book_class_columns(),
        data=classes.classes,
    )

    print(result["ot_class_uuid"])
    booking = await base_app.api.book_class(result["ot_class_uuid"])

    base_app.console.print(booking)


@bookings_app.command()
async def cancel_interactive() -> None:
    """
    Cancel a booking interactively
    """

    logger.info("Cancelling booking interactively")

    with base_app.console.status("Getting bookings...", spinner="arc"):
        if not base_app.api:
            base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)
        bookings = await base_app.api.get_bookings()

    result = prompt_select_from_table(
        console=base_app.console,
        prompt="Cancel a booking, any booking",
        columns=bookings.show_bookings_columns(),
        data=bookings.bookings,
    )

    print(result["class_booking_uuid"])
    booking = await base_app.api.cancel_booking(result["class_booking_uuid"])

    base_app.console.print(booking)


@bookings_app.command()
async def cancel(booking_uuid: str = typer.Option(help="Booking UUID to cancel")) -> None:
    """
    Cancel a booking
    """

    logger.info(f"Cancelling booking {booking_uuid}")

    if not base_app.api:
        base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)
    booking = await base_app.api.cancel_booking(booking_uuid)

    base_app.console.print(booking)


@classes_app.command(name="list")
async def list_classes(
    studio_uuids: list[str] = typer.Option(None, help="Studio UUIDs to get classes for"),
    include_home_studio: bool = typer.Option(True, help="Include the home studio in the classes"),
    start_date: str = typer.Option(default_factory=today, help="Start date for classes"),
    end_date: str = typer.Option(default_factory=next_month, help="End date for classes"),
    limit: int = typer.Option(None, help="Limit the number of classes returned"),
    class_type: ClassTypeCli = typer.Option(None, help="Class type to filter by"),
    exclude_cancelled: bool = typer.Option(
        True, "--exclude-cancelled/--allow-cancelled", help="Exclude cancelled classes", show_default=True
    ),
    exclude_none: bool = typer.Option(
        True, "--exclude-none/--allow-none", help="Exclude fields with a value of None", show_default=True
    ),
    output: OutputType = OPT_OUTPUT,
) -> None:
    """
    List classes data
    """

    logger.info("Listing classes")

    if output:
        base_app.output = output

    class_type_enum = ClassType.get_from_key_insensitive(class_type.value) if class_type else None

    if not base_app.api:
        base_app.api = await otf_api.Otf.create(base_app.username, base_app.password)
    classes = await base_app.api.get_classes(
        studio_uuids, include_home_studio, start_date, end_date, limit, class_type_enum, exclude_cancelled
    )

    if base_app.output == "json":
        base_app.print(classes.to_json(exclude_none=exclude_none))
    elif base_app.output == "table":
        base_app.print(classes.to_table())
    else:
        result = prompt_select_from_table(
            console=base_app.console,
            prompt="Book a class, any class",
            columns=classes.book_class_columns(),
            data=classes.classes,
        )
        print(type(result))
        print(result)
