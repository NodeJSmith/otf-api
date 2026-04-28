"""Tests for HttpxCognitoAuth in otf_api.auth.auth."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from otf_api.auth.auth import HttpxCognitoAuth

SIGV4AUTH_REQUIRED = "SIGV4AUTH_REQUIRED"


def _make_auth(id_token="test.id.token"):
    """Return an HttpxCognitoAuth with a pre-configured MagicMock cognito."""
    cognito = MagicMock()
    cognito.id_token = id_token
    cognito.check_token = MagicMock()
    return HttpxCognitoAuth(cognito=cognito)


def test_auth_flow_standard_request():
    """auth_flow sets Authorization: Bearer <id_token> and calls check_token(renew=True)."""
    auth = _make_auth()
    request = httpx.Request("GET", "https://api.example.com/")

    yielded = list(auth.auth_flow(request))

    assert len(yielded) == 1
    assert yielded[0].headers["Authorization"] == "Bearer test.id.token"
    auth.cognito.check_token.assert_called_once_with(renew=True)


def test_auth_flow_sigv4_branch():
    """auth_flow removes SIGV4AUTH_REQUIRED header and delegates to sign_httpx_request."""
    auth = _make_auth()
    request = httpx.Request("GET", "https://api.example.com/", headers={SIGV4AUTH_REQUIRED: "true"})

    signed_request = httpx.Request("GET", "https://api.example.com/")

    with patch.object(auth, "sign_httpx_request", return_value=iter([signed_request])) as mock_sign:
        yielded = list(auth.auth_flow(request))

    call_args = mock_sign.call_args
    passed_request = call_args[0][0]
    assert SIGV4AUTH_REQUIRED not in passed_request.headers
    assert passed_request.headers["Authorization"] == "Bearer test.id.token"
    auth.cognito.check_token.assert_called_once_with(renew=True)
    mock_sign.assert_called_once()
    assert yielded == [signed_request]


def test_auth_flow_token_not_string():
    """auth_flow raises ValueError when id_token is not a string."""
    auth = _make_auth(id_token=None)
    request = httpx.Request("GET", "https://api.example.com/")

    with pytest.raises(ValueError, match="Token is not a string"):
        list(auth.auth_flow(request))


def test_sign_httpx_request():
    """sign_httpx_request produces a request signed with AWS4-HMAC-SHA256."""
    cognito = MagicMock()
    cognito.get_identity_credentials.return_value = {
        "AccessKeyId": "AK",
        "SecretKey": "SK",
        "SessionToken": "ST",
    }
    auth = HttpxCognitoAuth(cognito=cognito)

    request = httpx.Request(
        "POST",
        "https://api.example.com/data",
        content=b'{"key": "value"}',
    )

    yielded = list(auth.sign_httpx_request(request))

    assert len(yielded) == 1
    signed = yielded[0]

    # connection header must be absent
    assert "connection" not in {h.lower() for h in signed.headers}

    # Authorization header must use AWS4-HMAC-SHA256 (SigV4 format)
    assert signed.headers["Authorization"].startswith("AWS4-HMAC-SHA256")

    # Result must be a new httpx.Request object
    assert isinstance(signed, httpx.Request)


def test_sign_httpx_request_streaming_body():
    """sign_httpx_request raises ValueError when the body has a .read attribute (streaming)."""
    cognito = MagicMock()
    auth = HttpxCognitoAuth(cognito=cognito)

    streaming_body = MagicMock()
    streaming_body.read = MagicMock()

    request = httpx.Request("POST", "https://api.example.com/data")
    # Replace the content with a streaming-like object
    request._content = streaming_body  # noqa: SLF001

    with pytest.raises(ValueError, match="Streaming bodies are not supported"):
        list(auth.sign_httpx_request(request))
