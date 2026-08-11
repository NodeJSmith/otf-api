"""Tests for Otf client lifecycle management (close / context manager)."""

from unittest.mock import patch

import pytest

from otf_api.api.api import Otf


def test_otf_close_closes_session(mock_user):
    with patch("otf_api.api.client.OtfUser", return_value=mock_user):
        otf = Otf(user=mock_user)

    session = otf._client.session
    assert not session.is_closed
    otf.close()
    assert session.is_closed


def test_otf_close_is_idempotent(mock_user):
    with patch("otf_api.api.client.OtfUser", return_value=mock_user):
        otf = Otf(user=mock_user)

    otf.close()
    otf.close()  # should not raise


def test_otf_context_manager(mock_user):
    with patch("otf_api.api.client.OtfUser", return_value=mock_user), Otf(user=mock_user) as otf:
        session = otf._client.session
        assert not session.is_closed

    assert session.is_closed


def test_otf_context_manager_closes_on_exception(mock_user):
    with (
        patch("otf_api.api.client.OtfUser", return_value=mock_user),
        pytest.raises(ValueError, match="boom"),
        Otf(user=mock_user) as otf,
    ):
        session = otf._client.session
        raise ValueError("boom")

    assert session.is_closed
