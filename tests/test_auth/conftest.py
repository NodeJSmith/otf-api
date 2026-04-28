"""Shared fixtures for auth test suite."""

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
