"""Tests for public error wrapping (OtfAuthenticationError, OtfTransportError)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from botocore.exceptions import ClientError

from otf_api.api.client import API_BASE_URL, OtfClient
from otf_api.exceptions import OtfAuthenticationError, OtfTransportError


def _make_mock_user() -> MagicMock:
    mock_user = MagicMock()
    mock_user.member_uuid = "test-uuid"
    mock_user.httpx_auth = None
    return mock_user


def _make_client_error(code: str = "NotAuthorizedException", message: str = "bad creds") -> ClientError:
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="InitiateAuth",
    )


class TestOtfAuthenticationError:
    def test_client_error_during_init_raises_auth_error(self):
        error = _make_client_error()
        with (
            patch("otf_api.auth.user.OtfCognito", side_effect=error),
            pytest.raises(OtfAuthenticationError) as exc_info,
        ):
            from otf_api.auth.user import OtfUser

            OtfUser(username="test@example.com", password="wrong")

        assert exc_info.value.__cause__ is error

    def test_client_error_during_fallback_raises_auth_error(self):
        call_count = 0
        error = _make_client_error()

        def cognito_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                from otf_api.exceptions import NoCredentialsError

                raise NoCredentialsError("no creds")
            raise error

        with (
            patch("otf_api.auth.user.OtfCognito", side_effect=cognito_side_effect),
            patch("otf_api.auth.user.get_username_password", return_value=("env@test.com", "pass")),
            pytest.raises(OtfAuthenticationError) as exc_info,
        ):
            from otf_api.auth.user import OtfUser

            OtfUser()

        assert exc_info.value.__cause__ is error

    def test_auth_error_is_subclass_of_otf_error(self):
        from otf_api.exceptions import OtfError

        assert issubclass(OtfAuthenticationError, OtfError)


class TestOtfTransportError:
    def test_timeout_raises_transport_error(self):
        mock_user = _make_mock_user()
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        timeout_error = httpx.ReadTimeout("timed out")
        with (
            respx.mock(assert_all_called=False, assert_all_mocked=True) as router,
            pytest.raises(OtfTransportError) as exc_info,
        ):
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=timeout_error)
            client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is timeout_error

    def test_connect_error_raises_transport_error(self):
        mock_user = _make_mock_user()
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        connect_error = httpx.ConnectError("connection refused")
        with (
            respx.mock(assert_all_called=False, assert_all_mocked=True) as router,
            pytest.raises(OtfTransportError) as exc_info,
        ):
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=connect_error)
            client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is connect_error

    def test_read_error_raises_transport_error(self):
        mock_user = _make_mock_user()
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        read_error = httpx.ReadError("connection reset")
        with (
            respx.mock(assert_all_called=False, assert_all_mocked=True) as router,
            pytest.raises(OtfTransportError) as exc_info,
        ):
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=read_error)
            client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is read_error

    def test_transport_error_is_subclass_of_otf_error(self):
        from otf_api.exceptions import OtfError

        assert issubclass(OtfTransportError, OtfError)
