import os
import typing
from collections.abc import Hashable

import readchar
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from otf_api.cli._utilities import exit_with_error
from otf_api.models.base import OtfBaseModel

if typing.TYPE_CHECKING:
    from rich.console import Console


def prompt(message, **kwargs):
    """Utility to prompt the user for input with consistent styling"""
    return Prompt.ask(f"[bold][green]?[/] {message}[/]", **kwargs)


def confirm(message, **kwargs):
    """Utility to prompt the user for confirmation with consistent styling"""
    return Confirm.ask(f"[bold][green]?[/] {message}[/]", **kwargs)


def prompt_select_from_list(console: "Console", prompt: str, options: list[str] | list[tuple[Hashable, str]]) -> str:
    """
    Given a list of options, display the values to user in a table and prompt them
    to select one.

    Args:
        options: A list of options to present to the user.
            A list of tuples can be passed as key value pairs. If a value is chosen, the
            key will be returned.

    Returns:
        str: the selected option
    """

    current_idx = 0
    selected_option = None

    def build_table() -> Table:
        """
        Generate a table of options. The `current_idx` will be highlighted.
        """

        table = Table(box=False, header_style=None, padding=(0, 0))
        table.add_column(
            f"? [bold]{prompt}[/] [bright_blue][Use arrows to move; enter to select]",
            justify="left",
            no_wrap=True,
        )

        for i, option in enumerate(options):
            if isinstance(option, tuple):
                option = option[1]

            if i == current_idx:
                # Use blue for selected options
                table.add_row("[bold][blue]> " + option)
            else:
                table.add_row("  " + option)
        return table

    with Live(build_table(), auto_refresh=False, console=console) as live:
        while selected_option is None:
            key = readchar.readkey()

            if key == readchar.key.UP:
                current_idx = current_idx - 1
                # wrap to bottom if at the top
                if current_idx < 0:
                    current_idx = len(options) - 1
            elif key == readchar.key.DOWN:
                current_idx = current_idx + 1
                # wrap to top if at the bottom
                if current_idx >= len(options):
                    current_idx = 0
            elif key == readchar.key.CTRL_C:
                # gracefully exit with no message
                exit_with_error("")
            elif key == readchar.key.ENTER or key == readchar.key.CR:
                selected_option = options[current_idx]
                if isinstance(selected_option, tuple):
                    selected_option = selected_option[0]

            live.update(build_table(), refresh=True)

        return selected_option


def prompt_select_from_table(
    console: "Console",
    prompt: str,
    columns: list[dict],
    data: list[OtfBaseModel],
    table_kwargs: dict | None = None,
) -> dict:
    """
    Given a list of columns and some data, display options to user in a table
    and prompt them to select one.

    Args:
        prompt: A prompt to display to the user before the table.
        columns: A list of dicts with keys `header` and `key` to display in
            the table. The `header` value will be displayed in the table header
            and the `key` value will be used to lookup the value for each row
            in the provided data.
        data: A list of dicts with keys corresponding to the `key` values in
            the `columns` argument.
        table_kwargs: Additional kwargs to pass to the `rich.Table` constructor.
    Returns:
        dict: Data representation of the selected row
    """
    current_idx = 0
    selected_row = None
    table_kwargs = table_kwargs or {}
    layout = Layout()

    layout.split_row(Layout(name="left"), Layout(name="right"))

    layout["left"].size = None
    layout["left"].ratio = 7
    layout["right"].size = None
    layout["right"].ratio = 3
    layout["right"].minimum_size = 50

    def build_table() -> Layout:
        """
        Generate a table of options. The `current_idx` will be highlighted.
        """

        # This would also get the height:
        # render_map = layout.render(console, console.options)
        # render_map[layout].region.height
        n_rows = os.get_terminal_size()[1] - 5

        table_kwargs.setdefault("expand", True)
        table = Table(**table_kwargs)
        table.add_column()
        for column in columns:
            table.add_column(column.get("header", ""))

        rows = {}
        max_length = 250
        for i, item in enumerate(data):
            id_val = item.id_val if hasattr(item, "id_val") else i
            if id_val not in rows:
                rows[id_val] = {"record": None, "item": item}

            rows[id_val]["record"] = tuple(
                (
                    value[:max_length] + "...\n"
                    if isinstance(value := item.get(column.get("key")), str) and len(value) > max_length
                    else value
                )
                for column in columns
            )

        if len(rows) > n_rows:
            start = max(0, current_idx - n_rows + 1)
            end = min(len(rows), start + n_rows)
            rows = dict(list(rows.items())[start:end])
            offset = start
        else:
            offset = 0

        selected_item = None
        for i, (id_val, row_data) in enumerate(rows.items()):
            row = row_data["record"]
            item = row_data["item"]
            idx_with_offset = i + offset
            row = list(map(str, row))
            if idx_with_offset == current_idx:
                selected_item = item
                # make whole row blue
                row = [f"[bold][blue]{cell}[/]" for cell in row]
                table.add_row("[bold][blue]> ", *row)
            elif hasattr(item, "is_booked") and item.is_booked:
                # make grey if already booked
                row = [f"[grey58]{cell}[/]" for cell in row]
                table.add_row("  ", *row)
            else:
                table.add_row("  ", *row)

        if table.row_count < n_rows:
            for _ in range(n_rows - table.row_count):
                table.add_row()

        layout["left"].update(Panel(table, title=prompt))
        layout["right"].update(Panel("", title="Selected Data"))
        if not selected_item:
            layout["right"].visible = False
        else:
            sidebar_data = selected_item.sidebar_data  # type: ignore
            layout["right"].update(sidebar_data)
            layout["right"].visible = True
        return layout

    with Live(build_table(), console=console, transient=True) as live:
        instructions_message = f"[bold][green]?[/] {prompt} [bright_blue][Use arrows to move; enter to select]"
        live.console.print(instructions_message)
        while selected_row is None:
            key = readchar.readkey()

            start_val = 0
            offset = 0
            if key in [readchar.key.UP, readchar.key.PAGE_UP]:
                offset = -1 if key == readchar.key.UP else -5
                start_val = len(data) - 1 if current_idx < 0 else current_idx
            elif key in [readchar.key.DOWN, readchar.key.PAGE_DOWN]:
                offset = 1 if key == readchar.key.DOWN else 5
                start_val = 0 if current_idx >= len(data) else current_idx
            elif key == readchar.key.CTRL_C:
                # gracefully exit with no message
                exit_with_error("")
            elif key == readchar.key.ENTER or key == readchar.key.CR:
                selected_row = data[current_idx]

            current_idx = start_val + offset

            live.update(build_table(), refresh=True)

        return selected_row
