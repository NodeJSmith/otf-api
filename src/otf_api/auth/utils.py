import os
import sys
from functools import partial
from getpass import getpass
from logging import getLogger

LOGGER = getLogger(__name__)
USERNAME_PROMPT = "Enter your Orangetheory Fitness username/email: "
PASSWORD_PROMPT = "Enter your Orangetheory Fitness password: "


def _show_error_message(message: str) -> None:
    try:
        from rich import get_console  # type: ignore

        get_console().print(message, style="bold red")
    except ImportError:
        print(message)


def _get_password_input(prompt: str) -> str:
    try:
        from rich import get_console  # type: ignore

        otf_input = partial(get_console().input, password=True)
        prompt = f"[bold blue]{prompt}[/bold blue]"
    except ImportError:
        otf_input = getpass

    return otf_input(prompt)


def _get_input(prompt: str) -> str:
    try:
        from rich import get_console  # type: ignore

        otf_input = get_console().input
        prompt = f"[bold blue]{prompt}[/bold blue]"
    except ImportError:
        otf_input = input

    return otf_input(prompt)


def _prompt_for_username() -> str:
    def get_username() -> str:
        username = _get_input(USERNAME_PROMPT)

        if not username:
            _show_error_message("Username is required")
            return ""

        if "@" not in username or username.endswith("@"):
            _show_error_message("Username should be a valid email address")
            return ""

        return username

    while not (username := get_username()):
        pass

    return username


def _prompt_for_password() -> str:
    def get_password() -> str:
        password = _get_password_input(PASSWORD_PROMPT)

        if not password:
            _show_error_message("Password is required")
            return ""

        return password

    while not (password := get_password()):
        pass

    return password


def get_credentials_from_env() -> tuple[str, str]:
    """Get credentials from environment variables.

    Returns:
        tuple[str, str]: A tuple containing the username and password.
    """

    username = os.getenv("OTF_EMAIL")
    password = os.getenv("OTF_PASSWORD")

    if not username or not password:
        _show_error_message("Environment variables OTF_EMAIL and OTF_PASSWORD are required")
        return "", ""

    return username, password


def prompt_for_username_and_password() -> tuple[str, str]:
    """Prompt for a username and password.

    Returns:
        tuple[str, str]: A tuple containing the username and password.
    """

    username = _prompt_for_username()
    password = _prompt_for_password()

    return username, password


def can_provide_input() -> bool:
    """Check if the script is running in an interactive shell.

    Returns:
        bool: True if the script is running in an interactive shell.
    """
    return os.isatty(sys.stdin.fileno()) and os.isatty(sys.stdout.fileno())
