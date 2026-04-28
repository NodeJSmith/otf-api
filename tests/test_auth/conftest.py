"""Shared fixtures for auth test suite."""

import time
from unittest.mock import MagicMock, patch

import jwt
import pytest

from otf_api.cache import OtfCache


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip OTF_EMAIL and OTF_PASSWORD from the environment."""
    monkeypatch.delenv("OTF_EMAIL", raising=False)
    monkeypatch.delenv("OTF_PASSWORD", raising=False)


@pytest.fixture()
def set_env_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set OTF_EMAIL and OTF_PASSWORD to known test values."""
    monkeypatch.setenv("OTF_EMAIL", "test@example.com")
    monkeypatch.setenv("OTF_PASSWORD", "test-password-123")


@pytest.fixture()
def tmp_cache(tmp_path):
    """Return an OtfCache instance backed by a temporary directory."""
    cache = OtfCache(str(tmp_path))
    yield cache
    cache.close()


@pytest.fixture()
def mock_cache(tmp_path):
    """Patch otf_api.auth.auth.CACHE with a fresh OtfCache backed by a temp directory."""
    cache = OtfCache(str(tmp_path))
    with patch("otf_api.auth.auth.CACHE", cache):
        yield cache
    cache.close()


@pytest.fixture()
def mock_idp_client():
    """Return a MagicMock pre-configured to stand in for the Cognito Identity Provider client."""
    client = MagicMock()
    client.confirm_device.return_value = {}
    client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "stub-access",
            "IdToken": "stub-id",
            "RefreshToken": "stub-refresh",
        }
    }
    return client


@pytest.fixture()
def mock_id_client():
    """Return a MagicMock pre-configured to stand in for the Cognito Identity client."""
    client = MagicMock()
    client.get_id.return_value = {"IdentityId": "us-east-1:test-id"}
    client.get_credentials_for_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIA_TEST",
            "SecretKey": "secret-test",
            "SessionToken": "session-test",
        }
    }
    return client


def fake_tokens(include_device_metadata=True):
    """Return a well-formed InitiateAuthResponseTypeDef dict with real JWT tokens."""
    future_exp = int(time.time()) + 3600
    payload = {"sub": "test-sub", "exp": future_exp, "iss": "test", "token_use": "access"}
    access_token = jwt.encode(payload, "test-secret", algorithm="HS256")

    id_payload = {"sub": "test-sub", "exp": future_exp, "iss": "test", "token_use": "id"}
    id_token = jwt.encode(id_payload, "test-secret", algorithm="HS256")

    auth_result = {
        "AccessToken": access_token,
        "IdToken": id_token,
        "RefreshToken": "test-refresh-token",
    }

    if include_device_metadata:
        auth_result["NewDeviceMetadata"] = {
            "DeviceKey": "us-east-1_test-device-key",
            "DeviceGroupKey": "test-device-group-key",
        }

    return {"AuthenticationResult": auth_result}


@pytest.fixture()
def mock_verify_token():
    """Patch pycognito.Cognito.verify_token with a side effect that mimics real behavior.

    The real verify_token sets `self.<id_name> = token` and `self.<token_use>_claims = decoded_payload`.
    Without this, _set_tokens will fail because access_token/id_token are not set after verify_token calls.
    """

    def _verify_token_side_effect(self, token, id_name, token_use):
        setattr(self, id_name, token)
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
        except Exception:
            decoded = {}
        setattr(self, f"{token_use}_claims", decoded)
        return decoded

    with patch("pycognito.Cognito.verify_token", _verify_token_side_effect):
        yield
