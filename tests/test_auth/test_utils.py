"""Tests for src/otf_api/auth/utils.py."""

from unittest.mock import patch

import pytest

from otf_api.auth.auth import NoCredentialsError
from otf_api.auth.utils import (
    _prompt_for_password,
    _prompt_for_username,
    can_provide_input,
    get_credentials_from_env,
    get_username_password,
    prompt_for_username_and_password,
)


def test_get_credentials_from_env_present(set_env_creds):
    username, password = get_credentials_from_env()
    assert username == "test@example.com"
    assert password == "test-password-123"


def test_get_credentials_from_env_missing_email(monkeypatch):
    monkeypatch.delenv("OTF_EMAIL", raising=False)
    monkeypatch.setenv("OTF_PASSWORD", "some-password")
    username, password = get_credentials_from_env()
    assert username == ""
    assert password == ""


def test_get_credentials_from_env_missing_password(monkeypatch):
    monkeypatch.setenv("OTF_EMAIL", "user@example.com")
    monkeypatch.delenv("OTF_PASSWORD", raising=False)
    username, password = get_credentials_from_env()
    assert username == ""
    assert password == ""


def test_get_credentials_from_env_both_missing(clean_env):
    username, password = get_credentials_from_env()
    assert username == ""
    assert password == ""


def test_can_provide_input_interactive():
    with (
        patch("sys.stdin") as mock_stdin,
        patch("sys.stdout") as mock_stdout,
        patch("os.isatty", return_value=True),
    ):
        mock_stdin.fileno.return_value = 0
        mock_stdout.fileno.return_value = 1
        assert can_provide_input() is True


def test_can_provide_input_non_interactive():
    with (
        patch("sys.stdin") as mock_stdin,
        patch("sys.stdout") as mock_stdout,
        patch("os.isatty", side_effect=lambda fd: fd != 0),
    ):
        mock_stdin.fileno.return_value = 0
        mock_stdout.fileno.return_value = 1
        assert can_provide_input() is False


def test_get_username_password_from_env(set_env_creds):
    with patch("otf_api.auth.utils._prompt_for_username") as mock_prompt:
        username, password = get_username_password()
    assert username == "test@example.com"
    assert password == "test-password-123"
    mock_prompt.assert_not_called()


def test_get_username_password_no_env_non_interactive(clean_env):
    with (
        patch("otf_api.auth.utils.can_provide_input", return_value=False),
        pytest.raises(NoCredentialsError),
    ):
        get_username_password()


def test_get_username_password_interactive_prompts(clean_env):
    with (
        patch("otf_api.auth.utils.can_provide_input", return_value=True),
        patch(
            "otf_api.auth.utils.prompt_for_username_and_password",
            return_value=("prompted@example.com", "prompted-pw"),
        ) as mock_prompt,
    ):
        username, password = get_username_password()
    assert username == "prompted@example.com"
    assert password == "prompted-pw"
    mock_prompt.assert_called_once()


def test_get_username_password_interactive_empty_response_raises(clean_env):
    with (
        patch("otf_api.auth.utils.can_provide_input", return_value=True),
        patch("otf_api.auth.utils.prompt_for_username_and_password", return_value=("", "")),
        pytest.raises(NoCredentialsError),
    ):
        get_username_password()


def test_prompt_for_username_retry_on_empty():
    with patch("otf_api.auth.utils._get_input", side_effect=["", "user@example.com"]):
        result = _prompt_for_username()
    assert result == "user@example.com"


def test_prompt_for_username_retry_on_invalid_email():
    with patch("otf_api.auth.utils._get_input", side_effect=["notanemail", "user@example.com"]):
        result = _prompt_for_username()
    assert result == "user@example.com"


def test_prompt_for_username_retry_on_trailing_at():
    with patch("otf_api.auth.utils._get_input", side_effect=["user@", "user@example.com"]):
        result = _prompt_for_username()
    assert result == "user@example.com"


def test_prompt_for_username_and_password():
    with (
        patch("otf_api.auth.utils._prompt_for_username", return_value="user@example.com"),
        patch("otf_api.auth.utils._prompt_for_password", return_value="mypassword"),
    ):
        username, password = prompt_for_username_and_password()
    assert username == "user@example.com"
    assert password == "mypassword"


def test_prompt_for_password_retry_on_empty():
    with patch("otf_api.auth.utils._get_password_input", side_effect=["", "mypassword"]):
        result = _prompt_for_password()
    assert result == "mypassword"
