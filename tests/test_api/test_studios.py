"""Tests for StudioApi read-only methods."""

import httpx

from otf_api.models.studios.studio_detail import StudioDetail
from otf_api.models.studios.studio_services import StudioService


def test_get_studio_detail(mock_otf) -> None:
    result = mock_otf.studios.get_studio_detail()

    assert isinstance(result, StudioDetail)
    assert isinstance(result.name, str)
    assert result.name != ""
    assert isinstance(result.studio_uuid, str)


def test_search_studios_by_geo(mock_otf) -> None:
    result = mock_otf.studios.search_studios_by_geo()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(s, StudioDetail) for s in result)

    first = result[0]
    assert isinstance(first.name, str)
    assert isinstance(first.studio_uuid, str)


def test_get_favorite_studios_empty(mock_otf) -> None:
    result = mock_otf.studios.get_favorite_studios()

    assert isinstance(result, list)
    assert result == []


def test_get_studio_detail_not_found_returns_empty(mock_otf, mock_router) -> None:
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    mock_router.request("GET", f"https://api.orangetheory.co/mobile/v1/studios/{fake_uuid}").mock(
        return_value=httpx.Response(404, json={"code": "NOT_FOUND", "message": "Studio not found"})
    )

    result = mock_otf.studios.get_studio_detail(fake_uuid)

    assert isinstance(result, StudioDetail)
    assert result.studio_uuid == fake_uuid
    assert result.name == "Studio Not Found"


def test_get_studio_services(mock_otf) -> None:
    result = mock_otf.studios.get_studio_services()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(s, StudioService) for s in result)

    first = result[0]
    assert isinstance(first.service_uuid, str)
    assert isinstance(first.name, str)
    assert first.studio is not None
    assert isinstance(first.studio.studio_uuid, str)
