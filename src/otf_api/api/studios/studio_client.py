from concurrent.futures import ThreadPoolExecutor
from typing import Any

from otf_api.api.client import CACHE, LOGGER, OtfClient


class StudioClient:
    """Client for retrieving studio and service data from the OTF API.

    This class provides methods to search for studios by geographic location, retrieve studio details,
    manage favorite studios, and get studio services.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    @CACHE.memoize(expire=600, tag="studio_detail", ignore=(0,))
    def get_studio_detail(self, studio_uuid: str) -> dict:
        """Retrieve raw studio details."""
        return self.client.default_request("GET", f"/mobile/v1/studios/{studio_uuid}")["data"]

    def _get_studios_by_geo(
        self, latitude: float | None, longitude: float | None, distance: int, page_index: int, page_size: int
    ) -> dict:
        """Retrieve raw studios by geo data."""
        return self.client.default_request(
            "GET",
            "/mobile/v1/studios",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "distance": distance,
                "pageIndex": page_index,
                "pageSize": page_size,
            },
        )

    def get_studios_by_geo(
        self, latitude: float | None, longitude: float | None, distance: int = 50
    ) -> list[dict[str, Any]]:
        """Searches for studios by geographic location.

        Args:
            latitude (float | None): Latitude of the location.
            longitude (float | None): Longitude of the location.
            distance (int): The distance in miles to search around the location. Default is 50.

        Returns:
            list[dict[str, Any]]: A list of studios within the specified distance from the given latitude and longitude.

        Raises:
            exc.OtfRequestError: If the request to the API fails.
        """
        distance = min(distance, 250)  # max distance is 250 miles
        page_size = 100
        page_index = 1
        LOGGER.debug(
            "Starting studio search",
            extra={
                "latitude": latitude,
                "longitude": longitude,
                "distance": distance,
                "page_index": page_index,
                "page_size": page_size,
            },
        )

        all_results: dict[str, dict[str, Any]] = {}

        while True:
            res = self._get_studios_by_geo(latitude, longitude, distance, page_index, page_size)

            studios = res["data"].get("studios", [])
            total_count = res["data"].get("pagination", {}).get("totalCount", 0)

            all_results.update({studio["studioUUId"]: studio for studio in studios})
            if len(all_results) >= total_count or not studios:
                break

            page_index += 1

        LOGGER.info("Studio search completed, fetched %d of %d studios", len(all_results), total_count, stacklevel=2)

        return list(all_results.values())

    def get_favorite_studios(self) -> dict:
        """Retrieve raw favorite studios data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/favorite-studios")["data"]

    def get_studio_services(self, studio_uuid: str) -> dict:
        """Retrieve raw studio services data."""
        return self.client.default_request("GET", f"/member/studios/{studio_uuid}/services")["data"]

    def post_favorite_studio(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from adding a studio to favorite studios."""
        return self.client.default_request(
            "POST", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids}
        )["data"]

    def delete_favorite_studio(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from removing a studio from favorite studios."""
        return self.client.default_request(
            "DELETE", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids}
        )

    def get_studio_detail_threaded(self, studio_uuids: list[str]) -> dict[str, dict[str, Any]]:
        """Get studio details in a ThreadPoolExecutor, to speed up the process.

        Args:
            studio_uuids (list[str]): The studio UUIDs to get.

        Returns:
            dict[str, dict[str, Any]]: A dictionary of studio details, keyed by studio UUID.
        """
        with ThreadPoolExecutor(max_workers=10) as pool:
            studios = pool.map(self.get_studio_detail, studio_uuids)

        studios_dict = {studio["studioUUId"]: studio for studio in studios}
        return studios_dict
