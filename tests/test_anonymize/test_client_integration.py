"""Integration tests verifying OtfClient hook injection behaviour.

These tests monkeypatch ``OtfUser`` to avoid real Cognito / network calls and
verify whether the anonymize hook is (or is not) injected into the httpx
session based on the ``OTF_ANONYMIZE_RESPONSES`` env var.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otf_api.anonymize.hooks import AnonymizedCaptureHook
from otf_api.api.client import OtfClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user() -> MagicMock:
    """Return a MagicMock that satisfies OtfClient's expectations for OtfUser."""
    mock_user = MagicMock()
    mock_user.member_uuid = "mock-member-uuid-1234-5678-9012"
    mock_user.httpx_auth = None  # httpx.Client accepts None for auth
    return mock_user


# ---------------------------------------------------------------------------
# test_env_var_disabled_no_hook
# ---------------------------------------------------------------------------


def test_env_var_disabled_no_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """When OTF_ANONYMIZE_RESPONSES is not set, no hook is injected."""
    monkeypatch.delenv("OTF_ANONYMIZE_RESPONSES", raising=False)

    with patch("otf_api.api.client.OtfUser", return_value=_make_mock_user()):

        client = OtfClient()

    assert not hasattr(client, "_anonymize_hook"), (
        "_anonymize_hook should not exist when OTF_ANONYMIZE_RESPONSES is not set"
    )
    hooks = client.session.event_hooks.get("response", [])
    assert not any(isinstance(h, AnonymizedCaptureHook) for h in hooks), (
        "No AnonymizedCaptureHook should be in session event hooks when disabled"
    )
    client.session.close()


def test_env_var_false_no_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """When OTF_ANONYMIZE_RESPONSES=false, no hook is injected."""
    monkeypatch.setenv("OTF_ANONYMIZE_RESPONSES", "false")

    with patch("otf_api.api.client.OtfUser", return_value=_make_mock_user()):

        client = OtfClient()

    assert not hasattr(client, "_anonymize_hook")
    client.session.close()


# ---------------------------------------------------------------------------
# test_env_var_injects_hook
# ---------------------------------------------------------------------------


def test_env_var_injects_hook(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When OTF_ANONYMIZE_RESPONSES=true, AnonymizedCaptureHook is injected."""
    monkeypatch.setenv("OTF_ANONYMIZE_RESPONSES", "true")
    # Use tmp_path so we don't pollute the real cache dir
    monkeypatch.setenv("OTF_ANONYMIZE_OUTPUT_DIR", str(tmp_path))

    with patch("otf_api.api.client.OtfUser", return_value=_make_mock_user()):

        client = OtfClient()

    assert hasattr(client, "_anonymize_hook"), (
        "_anonymize_hook should be set when OTF_ANONYMIZE_RESPONSES=true"
    )
    assert isinstance(client._anonymize_hook, AnonymizedCaptureHook)

    response_hooks = client.session.event_hooks.get("response", [])
    assert client._anonymize_hook in response_hooks, (
        "The hook instance should be in session.event_hooks['response']"
    )
    client.session.close()


def test_env_var_case_insensitive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """OTF_ANONYMIZE_RESPONSES=TRUE (uppercase) is accepted."""
    monkeypatch.setenv("OTF_ANONYMIZE_RESPONSES", "TRUE")
    monkeypatch.setenv("OTF_ANONYMIZE_OUTPUT_DIR", str(tmp_path))

    with patch("otf_api.api.client.OtfUser", return_value=_make_mock_user()):

        client = OtfClient()

    assert hasattr(client, "_anonymize_hook")
    client.session.close()
