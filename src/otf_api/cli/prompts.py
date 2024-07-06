import os
import typing

import readchar
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from otf_api.cli._utilities import exit_with_error
from otf_api.models.base import T

if typing.TYPE_CHECKING:
    from rich.console import Console


def prompt(message, **kwargs):
    """Utility to prompt the user for input with consistent styling"""
    return Prompt.ask(f"[bold][green]?[/] {message}[/]", **kwargs)


def confirm(message, **kwargs):
    """Utility to prompt the user for confirmation with consistent styling"""
    return Confirm.ask(f"[bold][green]?[/] {message}[/]", **kwargs)


def prompt_select_from_table(
    console: "Console",
    prompt: str,
    columns: list[str],
    data: list[T],
    table_kwargs: dict | None = None,
) -> dict:
    """
    Given a list of columns and some data, display options to user in a table
    and prompt them to select one.

    Args:
        prompt: A prompt to display to the user before the table.
        columns: A list of strings that represent the attributes of the data to display.
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

    if not data:
        exit_with_error("No data to display")

    MODEL_TYPE = type(data[0])

    TABLE_PANEL = Layout(name="left")
    DATA_PANEL = Layout(name="right")

    layout.split_row(TABLE_PANEL, DATA_PANEL)

    TABLE_PANEL.ratio = 7
    DATA_PANEL.ratio = 3
    DATA_PANEL.minimum_size = 50

    n_rows = os.get_terminal_size()[1] - 5

    def build_table() -> Layout:
        """
        Generate a table of options. The `current_idx` will be highlighted.
        """

        table = initialize_table()
        rows = data.copy()
        rows, offset = paginate_rows(rows)
        selected_item = add_rows_to_table(table, rows, offset)

        finalize_table(table, prompt, selected_item)

        return layout

    def initialize_table() -> Table:
        table_kwargs.setdefault("expand", True)
        table = Table(**table_kwargs)
        table.add_column()
        for column in columns:
            table.add_column(MODEL_TYPE.attr_to_column_header(column))
        return table

    def paginate_rows(rows: list[T]) -> tuple[list[T], int]:
        if len(rows) > n_rows:
            start = max(0, current_idx - n_rows + 1)
            end = min(len(rows), start + n_rows)
            rows = rows[start:end]
            offset = start
        else:
            offset = 0
        return rows, offset

    def add_rows_to_table(table: Table, rows: list[T], offset: int) -> T:
        selected_item: T = None
        for i, item in enumerate(rows):
            idx_with_offset = i + offset
            is_selected_row = idx_with_offset == current_idx
            if is_selected_row:
                selected_item = item
            table.add_row(*item.to_row(columns, is_selected_row))
        return selected_item

    def finalize_table(table: Table, prompt: str, selected_item: T) -> None:
        if table.row_count < n_rows:
            for _ in range(n_rows - table.row_count):
                table.add_row()

        TABLE_PANEL.update(Panel(table, title=prompt))
        DATA_PANEL.update(Panel("", title="Selected Data"))
        if not selected_item:
            DATA_PANEL.visible = False
        elif selected_item.sidebar_data is not None:
            sidebar_data = selected_item.sidebar_data
            DATA_PANEL.update(sidebar_data)
            DATA_PANEL.visible = True

    with Live(build_table(), console=console, transient=True) as live:
        instructions_message = f"[bold][green]?[/] {prompt} [bright_blue][Use arrows to move; enter to select]"
        live.console.print(instructions_message)
        while selected_row is None:
            key = readchar.readkey()

            start_val = 0
            offset = 0

            match key:
                case readchar.key.UP:
                    offset = -1
                    start_val = len(data) - 1 if current_idx < 0 else current_idx
                case readchar.key.PAGE_UP:
                    offset = -5
                    start_val = len(data) - 1 if current_idx < 0 else current_idx
                case readchar.key.DOWN:
                    offset = 1
                    start_val = 0 if current_idx >= len(data) else current_idx
                case readchar.key.PAGE_DOWN:
                    offset = 5
                    start_val = 0 if current_idx >= len(data) else current_idx
                case readchar.key.CTRL_C:
                    # gracefully exit with no message
                    exit_with_error("")
                case readchar.key.ENTER | readchar.key.CR:
                    selected_row = data[current_idx]

            current_idx = start_val + offset

            if current_idx < 0:
                current_idx = len(data) - 1
            elif current_idx >= len(data):
                current_idx = 0

            live.update(build_table(), refresh=True)

        return selected_row
