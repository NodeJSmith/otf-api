"""Tests for OtfCognito in src/otf_api/auth/auth.py."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError

from otf_api.auth.auth import NoCredentialsError, OtfCognito
from otf_api.exceptions import OtfAuthenticationError, OtfConfigurationError, OtfTransportError

from .conftest import fake_tokens


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_RESULT = fake_tokens(include_device_metadata=False)["AuthenticationResult"]
_ACCESS_TOKEN = _FAKE_RESULT["AccessToken"]
_ID_TOKEN = _FAKE_RESULT["IdToken"]


def _client_error(code, message=""):
    """Build a minimal botocore ClientError for the given error code."""
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="op",
    )


# ---------------------------------------------------------------------------
# Subtask 2 — __init__ cache-hit path
# ---------------------------------------------------------------------------


def test_init_cache_hit(mock_cache, mock_verify_token):
    """OtfCognito uses cached tokens when they are present and not expired."""
    tokens = fake_tokens(include_device_metadata=False)["AuthenticationResult"]
    access_token = tokens["AccessToken"]

    mock_cache.write_token_data_to_cache(
        {
            "access_token": access_token,
            "id_token": tokens["IdToken"],
            "refresh_token": tokens["RefreshToken"],
        }
    )
    mock_cache.write_device_data_to_cache(
        {"device_key": "dk-test", "device_group_key": "dgk-test", "device_password": "dp-test"}
    )

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    assert cognito.access_token == access_token


# ---------------------------------------------------------------------------
# Subtask 3 — __init__ no-credentials path
# ---------------------------------------------------------------------------


def test_init_no_credentials(mock_cache):
    """OtfCognito raises NoCredentialsError when no credentials are available."""
    with pytest.raises(NoCredentialsError):
        OtfCognito()


# ---------------------------------------------------------------------------
# Subtask 4 — get_decoded_access_token happy path
# ---------------------------------------------------------------------------


def test_get_decoded_access_token(mock_cache, mock_verify_token):
    """get_decoded_access_token returns a dict containing sub and exp."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    result = cognito.get_decoded_access_token()
    assert "sub" in result
    assert "exp" in result


# ---------------------------------------------------------------------------
# Subtask 5 — get_decoded_access_token no token
# ---------------------------------------------------------------------------


def test_get_decoded_access_token_no_token(mock_cache, mock_verify_token):
    """get_decoded_access_token raises AttributeError when access_token is None."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.access_token = None  # type: ignore

    with pytest.raises(AttributeError, match="Access Token Required"):
        cognito.get_decoded_access_token()


# ---------------------------------------------------------------------------
# Subtask 6 — expiration_seconds
# ---------------------------------------------------------------------------


def test_expiration_seconds(mock_cache, mock_verify_token):
    """expiration_seconds returns a positive value for a future-dated token."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    assert cognito.expiration_seconds > 0


# ---------------------------------------------------------------------------
# Subtask 7 — tokens property
# ---------------------------------------------------------------------------


def test_tokens_property(mock_cache, mock_verify_token):
    """tokens property returns only non-None token values."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": _ID_TOKEN, "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    tokens = cognito.tokens
    assert "access_token" in tokens
    assert "id_token" in tokens
    assert "refresh_token" in tokens

    # Excluding a None token
    cognito.refresh_token = None  # type: ignore
    tokens_no_refresh = cognito.tokens
    assert "refresh_token" not in tokens_no_refresh


# ---------------------------------------------------------------------------
# Subtask 8 — renew_access_token happy path
# ---------------------------------------------------------------------------


def test_renew_access_token(mock_cache, mock_verify_token, mock_idp_client):
    """renew_access_token calls initiate_auth with REFRESH_TOKEN_AUTH and DEVICE_KEY."""
    ft = fake_tokens()
    mock_idp_client.initiate_auth.return_value = ft

    mock_cache.write_token_data_to_cache(
        {"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "refresh-tok"}
    )
    mock_cache.write_device_data_to_cache({"device_key": "dk-123", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with patch.object(OtfCognito, "idp_client", new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_idp_client
        cognito.renew_access_token()

    mock_idp_client.initiate_auth.assert_called_once()
    call_kwargs = mock_idp_client.initiate_auth.call_args
    assert call_kwargs.kwargs["AuthFlow"] == "REFRESH_TOKEN_AUTH"
    assert call_kwargs.kwargs["AuthParameters"]["DEVICE_KEY"] == "dk-123"


# ---------------------------------------------------------------------------
# Subtask 9 — renew_access_token no device key
# ---------------------------------------------------------------------------


def test_renew_access_token_no_device_key(mock_cache, mock_verify_token):
    """renew_access_token raises ValueError when device_key is empty."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    # No device data

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.device_key = ""

    with pytest.raises(ValueError, match="Device key"):
        cognito.renew_access_token()


# ---------------------------------------------------------------------------
# Subtask 10 — renew_access_token no refresh token
# ---------------------------------------------------------------------------


def test_renew_access_token_no_refresh_token(mock_cache, mock_verify_token):
    """renew_access_token raises ValueError when refresh_token is None."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk-123", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.refresh_token = None  # type: ignore

    with pytest.raises(ValueError, match="refresh token"):
        cognito.renew_access_token()


# ---------------------------------------------------------------------------
# Subtask 11 — check_token NotAuthorizedException path
# ---------------------------------------------------------------------------


def test_check_token_not_authorized(mock_cache, mock_verify_token):
    """check_token raises NoCredentialsError and clears the cache on NotAuthorizedException."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with (
        patch("pycognito.Cognito.check_token", side_effect=_client_error("NotAuthorizedException")),
        patch.object(mock_cache, "clear") as mock_clear,
        pytest.raises(NoCredentialsError),
    ):
        cognito.check_token()

    mock_clear.assert_called_once()


def test_check_token_other_client_error_raises_auth_error(mock_cache, mock_verify_token):
    """check_token raises OtfAuthenticationError with a fixed, safe message for non-auth-expiry ClientErrors."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    error = _client_error("InternalErrorException", message="secret provider detail")
    with (
        patch("pycognito.Cognito.check_token", side_effect=error),
        pytest.raises(OtfAuthenticationError) as exc_info,
    ):
        cognito.check_token()

    assert str(exc_info.value) == "OTF authentication failed"
    assert "secret provider detail" not in str(exc_info.value)
    assert exc_info.value.__cause__ is error


def test_check_token_connectivity_failure_raises_transport_error(mock_cache, mock_verify_token):
    """check_token raises OtfTransportError with a fixed, safe message on refresh-time connectivity failures."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    error = EndpointConnectionError(endpoint_url="https://cognito-idp.example.com")
    with (
        patch("pycognito.Cognito.check_token", side_effect=error),
        pytest.raises(OtfTransportError) as exc_info,
    ):
        cognito.check_token()

    assert str(exc_info.value) == "OTF transport error"
    assert exc_info.value.__cause__ is error


def test_check_token_configuration_error_raises_configuration_error(mock_cache, mock_verify_token):
    """check_token raises OtfConfigurationError with a fixed, safe message on non-transport BotoCoreErrors."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    error = ParamValidationError(report="bad params")
    with (
        patch("pycognito.Cognito.check_token", side_effect=error),
        pytest.raises(OtfConfigurationError) as exc_info,
    ):
        cognito.check_token()

    assert str(exc_info.value) == "OTF configuration error"
    assert exc_info.value.__cause__ is error


# ---------------------------------------------------------------------------
# Subtask 12 — _set_tokens happy path
# ---------------------------------------------------------------------------


def test_set_tokens(mock_cache, mock_verify_token):
    """_set_tokens updates device_key, device_group_key, and writes tokens to cache."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    ft = fake_tokens(include_device_metadata=True)
    cognito._set_tokens(ft)

    assert cognito.device_key == "us-east-1_test-device-key"
    assert cognito.device_group_key == "test-device-group-key"

    cached_tokens = mock_cache.read_token_data_from_cache()
    assert "access_token" in cached_tokens


# ---------------------------------------------------------------------------
# Subtask 13 — _set_tokens missing AccessToken
# ---------------------------------------------------------------------------


def test_set_tokens_missing_access_token(mock_cache, mock_verify_token):
    """_set_tokens raises ValueError when AccessToken is absent from the result."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    ft = fake_tokens()
    del ft["AuthenticationResult"]["AccessToken"]

    with pytest.raises(ValueError, match="AccessToken"):
        cognito._set_tokens(ft)


# ---------------------------------------------------------------------------
# Subtask 14 — _handle_device_setup happy path
# ---------------------------------------------------------------------------


def test_handle_device_setup(mock_cache, mock_verify_token, mock_idp_client):
    """_handle_device_setup calls confirm_device and caches the device data."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache(
        {"device_key": "dk-test", "device_group_key": "dgk-test", "device_password": "dp-test"}
    )

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with (
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock) as mock_prop,
        patch(
            "otf_api.auth.auth.generate_hash_device",
            return_value=("test_password", {"PasswordVerifier": "x", "Salt": "y"}),
        ),
    ):
        mock_prop.return_value = mock_idp_client
        cognito._handle_device_setup()

    mock_idp_client.confirm_device.assert_called_once()
    cached = mock_cache.read_device_data_from_cache()
    assert cached.get("device_key") == "dk-test"
    assert cached.get("device_password") == "test_password"


# ---------------------------------------------------------------------------
# Subtask 15 — _handle_device_setup no device key
# ---------------------------------------------------------------------------


def test_handle_device_setup_no_device_key(mock_cache, mock_verify_token):
    """_handle_device_setup raises ValueError when device_key is not in the cache."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    # No device data in the cache

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with pytest.raises(ValueError, match="Device key"):
        cognito._handle_device_setup()


# ---------------------------------------------------------------------------
# Subtask 16 — login_with_password happy path
# ---------------------------------------------------------------------------


def test_login_with_password(mock_cache, mock_verify_token):
    """login_with_password calls AWSSRP.authenticate_user and sets tokens."""
    ft = fake_tokens()

    mock_aws = MagicMock()
    mock_aws.authenticate_user.return_value = ft

    with (
        patch("otf_api.auth.auth.AWSSRP", return_value=mock_aws) as MockAWSSRP,
        patch.object(OtfCognito, "_handle_device_setup"),
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock) as mock_idp_prop,
    ):
        mock_idp_prop.return_value = MagicMock()
        cognito = OtfCognito(username="user@test.com", password="password123")

    mock_aws.authenticate_user.assert_called_once()


# ---------------------------------------------------------------------------
# Subtask 17 — login_with_password UserLambdaValidationException retry
# ---------------------------------------------------------------------------


def test_login_with_password_lambda_validation_retry(mock_cache, mock_verify_token):
    """login_with_password retries once on UserLambdaValidationException."""
    ft = fake_tokens()

    mock_aws = MagicMock()
    mock_aws.authenticate_user.side_effect = [
        _client_error("UserLambdaValidationException", "UserLambdaValidationException occurred"),
        ft,
    ]

    with (
        patch("otf_api.auth.auth.AWSSRP", return_value=mock_aws),
        patch.object(OtfCognito, "_handle_device_setup"),
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock) as mock_idp_prop,
        patch("otf_api.auth.auth.sleep") as mock_sleep,
    ):
        mock_idp_prop.return_value = MagicMock()
        cognito = OtfCognito(username="user@test.com", password="password123")

    assert mock_aws.authenticate_user.call_count == 2
    mock_sleep.assert_called_once_with(5)


# ---------------------------------------------------------------------------
# Subtask 18 — login_with_password non-retryable ClientError
# ---------------------------------------------------------------------------


def test_login_with_password_non_retryable_error(mock_cache, mock_verify_token):
    """login_with_password propagates non-retryable ClientErrors unchanged."""
    mock_aws = MagicMock()
    mock_aws.authenticate_user.side_effect = _client_error("NotAuthorizedException", "Wrong password")

    with (
        patch("otf_api.auth.auth.AWSSRP", return_value=mock_aws),
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock) as mock_idp_prop,
        pytest.raises(ClientError),
    ):
        mock_idp_prop.return_value = MagicMock()
        OtfCognito(username="user@test.com", password="password123")


# ---------------------------------------------------------------------------
# Subtask 19 — get_identity_credentials
# ---------------------------------------------------------------------------


def test_get_identity_credentials(mock_cache, mock_verify_token, mock_id_client):
    """get_identity_credentials fetches identity pool credentials."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": _ID_TOKEN, "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with patch.object(OtfCognito, "id_client", new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_id_client
        creds = cognito.get_identity_credentials()

    assert creds["AccessKeyId"] == "AKIA_TEST"
    assert creds["SecretKey"] == "secret-test"
    assert creds["SessionToken"] == "session-test"
