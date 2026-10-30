"""Tests for OtfCognito in src/otf_api/auth/auth.py."""

# pyright: reportTypedDictNotRequiredAccess=none

import time
from unittest.mock import MagicMock, PropertyMock, patch

import jwt
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError, ProfileNotFound

from otf_api.auth.auth import NoCredentialsError, OtfCognito
from otf_api.exceptions import OtfAuthenticationError, OtfConfigurationError, OtfTransportError

from .conftest import fake_tokens


_FAKE_RESULT = fake_tokens(include_device_metadata=False)["AuthenticationResult"]
_ACCESS_TOKEN = _FAKE_RESULT["AccessToken"]
_ID_TOKEN = _FAKE_RESULT["IdToken"]


def _client_error(code, message=""):
    """Build a minimal botocore ClientError for the given error code."""
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="op",
    )


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


def test_init_no_credentials(mock_cache):
    """OtfCognito raises NoCredentialsError when no credentials are available."""
    with pytest.raises(NoCredentialsError):
        OtfCognito()


def test_get_decoded_access_token(mock_cache, mock_verify_token):
    """get_decoded_access_token returns a dict containing sub and exp."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    result = cognito.get_decoded_access_token()
    assert "sub" in result
    assert "exp" in result


def test_get_decoded_access_token_no_token(mock_cache, mock_verify_token):
    """get_decoded_access_token raises AttributeError when access_token is None."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.access_token = None  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(AttributeError, match="Access Token Required"):
        cognito.get_decoded_access_token()


def test_expiration_seconds(mock_cache, mock_verify_token):
    """expiration_seconds returns a positive value for a future-dated token."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    assert cognito.expiration_seconds > 0


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
    cognito.refresh_token = None
    tokens_no_refresh = cognito.tokens
    assert "refresh_token" not in tokens_no_refresh


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


def test_renew_access_token_no_device_key(mock_cache, mock_verify_token):
    """renew_access_token raises ValueError when device_key is empty."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    # No device data

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.device_key = ""

    with pytest.raises(ValueError, match="Device key"):
        cognito.renew_access_token()


def test_renew_access_token_no_refresh_token(mock_cache, mock_verify_token):
    """renew_access_token raises ValueError when refresh_token is None."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk-123", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    cognito.refresh_token = None

    with pytest.raises(ValueError, match="refresh token"):
        cognito.renew_access_token()


def _cognito_with_cached_tokens(mock_cache, access_token=_ACCESS_TOKEN):
    """Build an OtfCognito from cached tokens and device metadata, skipping the initial token check."""
    mock_cache.write_token_data_to_cache({"access_token": access_token, "id_token": "id", "refresh_token": "rt"})
    mock_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    with patch("pycognito.Cognito.check_token", return_value=False):
        return OtfCognito(username="user@test.com")


def test_renew_access_token_not_authorized(mock_cache, mock_verify_token, mock_idp_client):
    """renew_access_token raises NoCredentialsError and clears the cache on NotAuthorizedException."""
    cognito = _cognito_with_cached_tokens(mock_cache)
    error = _client_error("NotAuthorizedException")
    mock_idp_client.initiate_auth.side_effect = error

    with (
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock, return_value=mock_idp_client),
        patch.object(mock_cache, "clear") as mock_clear,
        pytest.raises(NoCredentialsError) as exc_info,
    ):
        cognito.renew_access_token()

    mock_clear.assert_called_once()
    assert exc_info.value.__cause__ is error


def test_renew_access_token_other_client_error_raises_auth_error(mock_cache, mock_verify_token, mock_idp_client):
    """renew_access_token raises OtfAuthenticationError with a fixed, safe message for other ClientErrors."""
    cognito = _cognito_with_cached_tokens(mock_cache)
    error = _client_error("InternalErrorException", message="secret provider detail")
    mock_idp_client.initiate_auth.side_effect = error

    with (
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock, return_value=mock_idp_client),
        pytest.raises(OtfAuthenticationError) as exc_info,
    ):
        cognito.renew_access_token()

    assert str(exc_info.value) == "OTF authentication failed"
    assert "secret provider detail" not in str(exc_info.value)
    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize(
    ("error", "expected_type", "expected_message"),
    [
        (
            EndpointConnectionError(endpoint_url="https://cognito-idp.example.com"),
            OtfTransportError,
            "OTF transport error",
        ),
        (ParamValidationError(report="bad params"), OtfConfigurationError, "OTF configuration error"),
    ],
)
def test_renew_access_token_botocore_error(
    mock_cache, mock_verify_token, mock_idp_client, error, expected_type, expected_message
):
    """renew_access_token maps BotoCoreErrors to OtfTransportError or OtfConfigurationError."""
    cognito = _cognito_with_cached_tokens(mock_cache)
    mock_idp_client.initiate_auth.side_effect = error

    with (
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock, return_value=mock_idp_client),
        pytest.raises(expected_type) as exc_info,
    ):
        cognito.renew_access_token()

    assert str(exc_info.value) == expected_message
    assert exc_info.value.__cause__ is error


def test_check_token_expired_not_authorized(mock_cache, mock_verify_token, mock_idp_client):
    """check_token on an expired token surfaces renew_access_token's NoCredentialsError and clears the cache."""
    expired = jwt.encode({"sub": "test-sub", "exp": int(time.time()) - 60}, "test-secret", algorithm="HS256")
    cognito = _cognito_with_cached_tokens(mock_cache, access_token=expired)
    mock_idp_client.initiate_auth.side_effect = _client_error("NotAuthorizedException")

    with (
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock, return_value=mock_idp_client),
        patch.object(mock_cache, "clear") as mock_clear,
        pytest.raises(NoCredentialsError),
    ):
        cognito.check_token()

    mock_clear.assert_called_once()


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


def test_handle_device_setup_no_device_key(mock_cache, mock_verify_token):
    """_handle_device_setup raises ValueError when device_key is not in the cache."""
    mock_cache.write_token_data_to_cache({"access_token": _ACCESS_TOKEN, "id_token": "id", "refresh_token": "rt"})
    # No device data in the cache

    with patch("pycognito.Cognito.check_token", return_value=False):
        cognito = OtfCognito(username="user@test.com")

    with pytest.raises(ValueError, match="Device key"):
        cognito._handle_device_setup()


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


def _construct_with_password(mock_idp_client, authenticate_user_side_effect):
    """Construct OtfCognito with a password; AWSSRP.authenticate_user yields authenticate_user_side_effect."""
    mock_aws = MagicMock()
    mock_aws.authenticate_user.side_effect = authenticate_user_side_effect

    with (
        patch("otf_api.auth.auth.AWSSRP", return_value=mock_aws),
        patch.object(OtfCognito, "idp_client", new_callable=PropertyMock, return_value=mock_idp_client),
        patch("otf_api.auth.auth.sleep"),
    ):
        OtfCognito(username="user@test.com", password="pw")


def test_login_with_password_non_retryable_error(mock_cache, mock_verify_token, mock_idp_client):
    """login_with_password raises OtfAuthenticationError with a fixed, safe message for non-retryable ClientErrors."""
    error = _client_error("NotAuthorizedException", "Wrong password")

    with pytest.raises(OtfAuthenticationError) as exc_info:
        _construct_with_password(mock_idp_client, error)

    assert str(exc_info.value) == "OTF authentication failed"
    assert "Wrong password" not in str(exc_info.value)
    assert exc_info.value.__cause__ is error


def test_login_with_password_retry_failure_raises_auth_error(mock_cache, mock_verify_token, mock_idp_client):
    """A ClientError from the UserLambdaValidationException retry is mapped to OtfAuthenticationError."""
    retry_error = _client_error("InternalErrorException", "secret provider detail")
    side_effects = [_client_error("UserLambdaValidationException", "UserLambdaValidationException"), retry_error]

    with pytest.raises(OtfAuthenticationError) as exc_info:
        _construct_with_password(mock_idp_client, side_effects)

    assert exc_info.value.__cause__ is retry_error


@pytest.mark.parametrize(
    ("error", "expected_type", "expected_message"),
    [
        (
            EndpointConnectionError(endpoint_url="https://cognito-idp.example.com"),
            OtfTransportError,
            "OTF transport error",
        ),
        (ParamValidationError(report="bad params"), OtfConfigurationError, "OTF configuration error"),
    ],
)
def test_login_with_password_botocore_error(
    mock_cache, mock_verify_token, mock_idp_client, error, expected_type, expected_message
):
    """login_with_password maps BotoCoreErrors to OtfTransportError or OtfConfigurationError."""
    with pytest.raises(expected_type) as exc_info:
        _construct_with_password(mock_idp_client, error)

    assert str(exc_info.value) == expected_message
    assert exc_info.value.__cause__ is error


def test_login_with_password_device_confirmation_error(mock_cache, mock_verify_token, mock_idp_client):
    """A ClientError from confirm_device during login is mapped to OtfAuthenticationError."""
    error = _client_error("InvalidParameterException", "secret provider detail")
    mock_idp_client.confirm_device.side_effect = error

    with pytest.raises(OtfAuthenticationError) as exc_info:
        _construct_with_password(mock_idp_client, [fake_tokens()])

    assert exc_info.value.__cause__ is error


def test_login_with_password_client_construction_error(mock_cache, mock_verify_token):
    """A BotoCoreError from building the real idp_client during login is mapped to OtfConfigurationError."""
    error = ProfileNotFound(profile="missing")

    with (
        patch("otf_api.auth.auth.Session", side_effect=error),
        pytest.raises(OtfConfigurationError) as exc_info,
    ):
        OtfCognito(username="user@test.com", password="pw")

    assert exc_info.value.__cause__ is error


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


@pytest.mark.parametrize(
    ("error", "expected_type", "expected_message"),
    [
        (_client_error("NotAuthorizedException", "secret provider detail"), OtfAuthenticationError, "OTF authentication failed"),
        (EndpointConnectionError(endpoint_url="https://cognito-identity.example.com"), OtfTransportError, "OTF transport error"),
        (ParamValidationError(report="bad params"), OtfConfigurationError, "OTF configuration error"),
    ],
)
def test_get_identity_credentials_error(
    mock_cache, mock_verify_token, mock_id_client, error, expected_type, expected_message
):
    """get_identity_credentials maps ClientError and BotoCoreError to fixed-message Otf* errors."""
    cognito = _cognito_with_cached_tokens(mock_cache)
    mock_id_client.get_id.side_effect = error

    with (
        patch.object(OtfCognito, "id_client", new_callable=PropertyMock, return_value=mock_id_client),
        pytest.raises(expected_type) as exc_info,
    ):
        cognito.get_identity_credentials()

    assert str(exc_info.value) == expected_message
    assert exc_info.value.__cause__ is error


def test_get_identity_credentials_client_construction_error(mock_cache, mock_verify_token):
    """A BotoCoreError from building the real id_client is mapped to OtfConfigurationError."""
    cognito = _cognito_with_cached_tokens(mock_cache)
    error = ProfileNotFound(profile="missing")

    with (
        patch("otf_api.auth.auth.Session", side_effect=error),
        pytest.raises(OtfConfigurationError) as exc_info,
    ):
        cognito.get_identity_credentials()

    assert exc_info.value.__cause__ is error
