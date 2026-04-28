"""Tests for OtfUser in otf_api.auth.user."""

from unittest.mock import MagicMock, patch

import pytest

from otf_api.auth.auth import NoCredentialsError, HttpxCognitoAuth
from otf_api.auth.user import OtfUser


def _make_cognito_mock(
    access_claims=None,
    id_claims=None,
):
    """Return a MagicMock configured to behave like OtfCognito."""
    mock = MagicMock()
    mock.access_claims = access_claims or {"sub": "test-cognito-id"}
    mock.id_claims = id_claims or {
        "cognito:username": "test-uuid",
        "email": "test@example.com",
    }
    return mock


def test_otf_user_init_happy_path():
    """OtfUser extracts cognito_id, member_uuid, email_address from cognito claims."""
    cognito_mock = _make_cognito_mock(
        access_claims={"sub": "test-cognito-id"},
        id_claims={"cognito:username": "test-uuid", "email": "test@example.com"},
    )

    with patch("otf_api.auth.user.OtfCognito", return_value=cognito_mock):
        user = OtfUser(username="test@example.com", password="secret")

    assert user.cognito_id == "test-cognito-id"
    assert user.member_uuid == "test-uuid"
    assert user.email_address == "test@example.com"
    assert isinstance(user.httpx_auth, HttpxCognitoAuth)
    assert user.httpx_auth.cognito is cognito_mock


def test_otf_user_init_no_credentials_fallback():
    """OtfUser falls back to env credentials when first OtfCognito call raises NoCredentialsError."""
    second_mock = _make_cognito_mock(
        access_claims={"sub": "env-cognito-id"},
        id_claims={"cognito:username": "env-uuid", "email": "env@example.com"},
    )

    call_count = 0

    def cognito_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise NoCredentialsError("no creds")
        return second_mock

    with (
        patch("otf_api.auth.user.OtfCognito", side_effect=cognito_side_effect) as mock_cognito,
        patch("otf_api.auth.user.get_username_password", return_value=("env@example.com", "envpass")) as mock_get_creds,
    ):
        user = OtfUser()

    # get_username_password was called after the first failure
    mock_get_creds.assert_called_once()

    # Second OtfCognito call received the env credentials
    second_call_kwargs = mock_cognito.call_args_list[1][1]
    assert second_call_kwargs["username"] == "env@example.com"
    assert second_call_kwargs["password"] == "envpass"

    assert user.cognito_id == "env-cognito-id"
    assert user.member_uuid == "env-uuid"
    assert user.email_address == "env@example.com"


def test_otf_user_init_unexpected_error_propagates():
    """OtfUser propagates unexpected errors (non-NoCredentialsError) from OtfCognito."""
    with patch("otf_api.auth.user.OtfCognito", side_effect=ValueError("unexpected")):
        with pytest.raises(ValueError, match="unexpected"):
            OtfUser(username="test@example.com", password="secret")
