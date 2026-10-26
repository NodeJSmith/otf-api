"""Tests for public error wrapping (OtfAuthenticationError, OtfTransportError)."""

from typing import Never
from unittest.mock import patch

import httpx
import pytest
import respx

from otf_api.api.client import API_BASE_URL, OtfClient
from otf_api.auth.user import OtfUser
from otf_api.exceptions import (
    NoCredentialsError,
    OtfAuthenticationError,
    OtfConfigurationError,
    OtfError,
    OtfTransportError,
)


class TestOtfAuthenticationError:
    @pytest.mark.parametrize(
        "error",
        [
            OtfAuthenticationError("OTF authentication failed"),
            OtfTransportError("OTF transport error"),
            OtfConfigurationError("OTF configuration error"),
        ],
    )
    def test_cognito_error_during_init_propagates_unchanged(self, error: OtfError):
        with (
            patch("otf_api.auth.user.OtfCognito", side_effect=error),
            pytest.raises(type(error)) as exc_info,
        ):
            OtfUser(username="test@example.com", password="wrong")

        assert exc_info.value is error

    def test_auth_error_during_fallback_propagates_unchanged(self):
        call_count = 0
        error = OtfAuthenticationError("OTF authentication failed")

        def cognito_side_effect(**kwargs: object) -> Never:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NoCredentialsError("no creds")
            raise error

        with (
            patch("otf_api.auth.user.OtfCognito", side_effect=cognito_side_effect),
            patch("otf_api.auth.user.get_username_password", return_value=("env@test.com", "pass")),
            pytest.raises(OtfAuthenticationError) as exc_info,
        ):
            OtfUser()

        assert exc_info.value is error

    def test_auth_error_is_subclass_of_otf_error(self):
        assert issubclass(OtfAuthenticationError, OtfError)


class TestOtfTransportError:
    def test_timeout_raises_transport_error(self, mock_user):
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        timeout_error = httpx.ReadTimeout("timed out")
        with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=timeout_error)
            with pytest.raises(OtfTransportError) as exc_info:
                client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is timeout_error

    def test_connect_error_raises_transport_error(self, mock_user):
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        connect_error = httpx.ConnectError("connection refused")
        with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=connect_error)
            with pytest.raises(OtfTransportError) as exc_info:
                client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is connect_error

    def test_read_error_raises_transport_error(self, mock_user):
        with patch("otf_api.api.client.OtfUser", return_value=mock_user):
            client = OtfClient(user=mock_user)

        read_error = httpx.ReadError("connection reset")
        with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
            router.get(f"https://{API_BASE_URL}/test").mock(side_effect=read_error)
            with pytest.raises(OtfTransportError) as exc_info:
                client.do("GET", API_BASE_URL, "/test")

        assert exc_info.value.__cause__ is read_error

    def test_transport_error_is_subclass_of_otf_error(self):
        assert issubclass(OtfTransportError, OtfError)


class TestOtfConfigurationError:
    def test_configuration_error_is_subclass_of_otf_error(self):
        assert issubclass(OtfConfigurationError, OtfError)
