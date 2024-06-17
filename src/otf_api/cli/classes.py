import pendulum
import typer
from loguru import logger

import otf_api
from otf_api.cli.app import OPT_OUTPUT, AsyncTyper, OutputType, base_app

classes_app = AsyncTyper(name="classes", help="Get classes data")
base_app.add_typer(classes_app, aliases=["booking"])


def today() -> str:
    val: str = pendulum.yesterday().date().to_date_string()
    return val


def next_month() -> str:
    val: str = pendulum.now().add(months=1).date().to_date_string()
    return val


@classes_app.command(aliases=["ls", "list"])
async def list_classes(
    studio_uuids: list[str] = typer.Option(None, help="Studio UUIDs to get classes for"),
    include_home_studio: bool = typer.Option(True, help="Include the home studio in the classes"),
    start_date: str = typer.Option(default_factory=today, help="Start date for classes"),
    end_date: str = typer.Option(default_factory=next_month, help="End date for classes"),
    limit: int = typer.Option(None, help="Limit the number of classes returned"),
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

    if not base_app.api:
        base_app.api = await otf_api.Api.create(base_app.username, base_app.password)
    classes = await base_app.api.classes_api.get_classes(studio_uuids, include_home_studio, start_date, end_date, limit)

    kwargs = {"indent": 4, "exclude_none": exclude_none}

    if base_app.output == "json":
        base_app.print(classes.model_dump_json(**kwargs))
    elif base_app.output == "table":
        base_app.print(classes.to_table())
