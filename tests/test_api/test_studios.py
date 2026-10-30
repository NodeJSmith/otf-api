"""Tests for StudioApi read-only methods."""

from unittest.mock import patch

import httpx
import pytest
from conftest import load_fixture

from otf_api.models.studios import StudioStatus
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


def test_get_studio_detail_keeps_unrecognized_status(mock_otf, mock_router) -> None:
    uuid = "11111111-1111-1111-1111-111111111111"
    fixture_data = load_fixture("studios/get_studio_detail__452ec40a")
    fixture_data["data"]["studioUUId"] = uuid
    fixture_data["data"]["studioStatus"] = "Relocating"
    mock_router.request("GET", f"https://api.orangetheory.co/mobile/v1/studios/{uuid}").mock(
        return_value=httpx.Response(200, json=fixture_data)
    )

    result = mock_otf.studios.get_studio_detail(uuid)

    assert result.status == "Relocating"
    assert not isinstance(result.status, StudioStatus)


@pytest.mark.parametrize(
    ["raw", "expected"],
    [("Active", StudioStatus.ACTIVE), (None, None)],
)
def test_studio_status_known_value_and_null_pass_through(raw, expected) -> None:
    result = StudioDetail.model_validate({"studioUUId": "uuid", "studioStatus": raw})

    assert result.status is expected


def test_null_studio_status_is_not_reported() -> None:
    with patch("otf_api.models.vocabulary.LOGGER.warning") as warning:
        StudioDetail.model_validate({"studioUUId": "uuid", "studioStatus": None})

    warning.assert_not_called()


def test_get_studio_detail_threaded_skips_invalid_uuid(mock_otf) -> None:
    valid_uuid = mock_otf.studios.get_studio_detail().studio_uuid

    result = mock_otf.studios.client.get_studio_detail_threaded([valid_uuid, "../invalid"])

    assert list(result) == [valid_uuid]
