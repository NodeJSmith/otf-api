"""Shared fixtures for API tests — mock Otf client with respx HTTP interception."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from conftest import FIXTURE_INDEX, MOCK_COGNITO_ID, MOCK_MEMBER_UUID, load_fixture

from otf_api.api.api import Otf
from otf_api.api.members.member_client import MemberClient
from otf_api.api.studios.studio_client import StudioClient
from otf_api.api.workouts.workout_client import WorkoutClient


def _make_mock_user() -> MagicMock:
    """Create a mock OtfUser that bypasses Cognito auth."""
    mock_user = MagicMock()
    mock_user.member_uuid = MOCK_MEMBER_UUID
    mock_user.cognito_id = MOCK_COGNITO_ID
    mock_user.email_address = "anthony86@example.org"
    mock_user.httpx_auth = None  # httpx.Client accepts None
    return mock_user


def _build_full_url(entry: dict) -> str:
    """Build the full URL for a fixture index entry."""
    path = entry["path"]
    params = entry["params"]
    base = f"https://{entry['host']}{path}"
    if params:
        return f"{base}?{params}"
    return base


def _register_routes(router: respx.MockRouter) -> None:
    """Register all fixture routes on the respx router.

    Deduplicates entries that share the exact same (host, path, params) key,
    keeping the first occurrence.
    """
    seen: set[str] = set()
    for entry in FIXTURE_INDEX:
        url = _build_full_url(entry)
        if url in seen:
            continue
        seen.add(url)

        # Load fixture body (file is e.g. "members/get_member_detail.json")
        fixture_name = entry["file"].removesuffix(".json")
        fixture_data = load_fixture(fixture_name)

        method = entry["method"].upper()
        status = entry.get("status", 200)

        router.request(method, url).mock(
            return_value=httpx.Response(status, json=fixture_data)
        )


# Methods decorated with @CACHE.memoize() whose closures hold the import-time cache.
# We bypass the memoize layer for tests by replacing them with their __wrapped__ originals.
_MEMOIZED_METHODS: list[tuple[type, str]] = [
    (MemberClient, "get_member_detail"),
    (StudioClient, "get_studio_detail"),
    (WorkoutClient, "get_performance_summary"),
    (WorkoutClient, "get_telemetry"),
]


@pytest.fixture()
def mock_user():
    """Yield a mock OtfUser that bypasses Cognito auth."""
    return _make_mock_user()


@pytest.fixture()
def mock_router():
    """Yield a started respx MockRouter with all fixture routes registered."""
    router = respx.MockRouter(assert_all_called=False, assert_all_mocked=True)
    _register_routes(router)
    router.start()
    yield router
    router.stop()


@pytest.fixture()
def mock_otf(mock_router):
    """Yield a fully wired Otf instance with auth bypassed and HTTP intercepted.

    - OtfUser is replaced with a MagicMock (no Cognito calls)
    - respx intercepts all HTTP with assert_all_mocked=True
    - @CACHE.memoize() decorated methods are replaced with their unwrapped originals
      to avoid pickle failures caused by MagicMock objects in the cache key
    """
    mock_user = _make_mock_user()

    memoize_patches = [
        patch.object(cls, method_name, cls.__dict__[method_name].__wrapped__)
        for cls, method_name in _MEMOIZED_METHODS
    ]

    with patch("otf_api.api.client.OtfUser", return_value=mock_user):
        for p in memoize_patches:
            p.start()

        try:
            otf = Otf(user=mock_user)
            yield otf
        finally:
            for p in memoize_patches:
                p.stop()
