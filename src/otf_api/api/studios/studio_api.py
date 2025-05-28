import typing
from logging import getLogger

from otf_api import exceptions as exc
from otf_api import models
from otf_api.api import utils
from otf_api.api.client import OtfClient

from .studio_client import StudioClient

if typing.TYPE_CHECKING:
    from otf_api import Otf

LOGGER = getLogger(__name__)


class StudioApi:
    def __init__(self, otf: "Otf", otf_client: OtfClient):
        """Initialize the Studio API client.

        Args:
            otf (Otf): The OTF API client.
            otf_client (OtfClient): The OTF client to use for requests.
        """
        self.otf = otf
        self.client = StudioClient(otf_client)

    def get_favorite_studios(self) -> list[models.StudioDetail]:
        """Get the member's favorite studios.

        Returns:
            list[StudioDetail]: The member's favorite studios.
        """
        data = self.client.get_favorite_studios()
        studio_uuids = [studio["studioUUId"] for studio in data]
        return [self.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids]

    def add_favorite_studio(self, studio_uuids: list[str] | str) -> list[models.StudioDetail]:
        """Add a studio to the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to add to the member's favorite\
            studios. If a string is provided, it will be converted to a list.

        Returns:
            list[StudioDetail]: The new favorite studios.
        """
        studio_uuids = utils.ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        resp = self.client.post_favorite_studio(studio_uuids)
        if not resp:
            return []

        new_faves = resp.get("studios", [])

        return [models.StudioDetail.create(**studio, api=self.otf) for studio in new_faves]

    def remove_favorite_studio(self, studio_uuids: list[str] | str) -> None:
        """Remove a studio from the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to remove from the member's\
            favorite studios. If a string is provided, it will be converted to a list.

        Returns:
            None
        """
        studio_uuids = utils.ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        # keeping the convention of regular/raw methods even though this method doesn't return anything
        # in case that changes in the future
        self.client.delete_favorite_studio(studio_uuids)

    def get_studio_services(self, studio_uuid: str | None = None) -> list[models.StudioService]:
        """Get the services available at a specific studio.

        If no studio UUID is provided, the member's home studio will be used.

        Args:
            studio_uuid (str, optional): The studio UUID to get services for.

        Returns:
            list[StudioService]: The services available at the studio.
        """
        studio_uuid = studio_uuid or self.otf.home_studio_uuid
        data = self.client.get_studio_services(studio_uuid)

        for d in data:
            d["studio"] = self.get_studio_detail(studio_uuid)

        return [models.StudioService(**d) for d in data]

    def get_studio_detail(self, studio_uuid: str | None = None) -> models.StudioDetail:
        """Get detailed information about a specific studio.

        If no studio UUID is provided, it will default to the user's home studio.

        If the studio is not found, it will return a StudioDetail object with default values.

        Args:
            studio_uuid (str, optional): The studio UUID to get detailed information about.

        Returns:
            StudioDetail: Detailed information about the studio.
        """
        studio_uuid = studio_uuid or self.otf.home_studio_uuid

        try:
            res = self.client.get_studio_detail(studio_uuid)
        except exc.ResourceNotFoundError:
            return models.StudioDetail.create_empty_model(studio_uuid)

        return models.StudioDetail.create(**res, api=self.otf)

    def get_studios_by_geo(
        self, latitude: float | None = None, longitude: float | None = None
    ) -> list[models.StudioDetail]:
        """Alias for search_studios_by_geo."""
        return self.search_studios_by_geo(latitude, longitude)

    def search_studios_by_geo(
        self, latitude: float | None = None, longitude: float | None = None, distance: int = 50
    ) -> list[models.StudioDetail]:
        """Search for studios by geographic location.

        Args:
            latitude (float, optional): Latitude of the location to search around, if None uses home studio latitude.
            longitude (float, optional): Longitude of the location to search around, if None uses home studio longitude.
            distance (int, optional): The distance in miles to search around the location. Default is 50.

        Returns:
            list[StudioDetail]: List of studios that match the search criteria.
        """
        latitude = latitude or self.otf.home_studio.location.latitude
        longitude = longitude or self.otf.home_studio.location.longitude

        results = self.client.get_studios_by_geo(latitude, longitude, distance)
        return [models.StudioDetail.create(**studio, api=self.otf) for studio in results]

    def _get_all_studios(self) -> list[models.StudioDetail]:
        """Gets all studios. Marked as private to avoid random users calling it.

        Useful for testing and validating models.

        Returns:
            list[StudioDetail]: List of studios that match the search criteria.
        """
        # long/lat being None will cause the endpoint to return all studios
        results = self.client.get_studios_by_geo(None, None)
        return [models.StudioDetail.create(**studio, api=self.otf) for studio in results]

    def _get_studio_detail_threaded(self, studio_uuids: list[str]) -> dict[str, models.StudioDetail]:
        """Get detailed information about multiple studios in a threaded manner.

        This is used to improve performance when fetching details for multiple studios at once.
        This method is on the Otf class because StudioDetail is a model that requires the API instance.

        Args:
            studio_uuids (list[str]): List of studio UUIDs to get details for.

        Returns:
            dict[str, StudioDetail]: A dictionary mapping studio UUIDs to their detailed information.
        """
        studio_dicts = self.client.get_studio_detail_threaded(studio_uuids)
        return {
            studio_uuid: models.StudioDetail.create(**studio, api=self.otf)
            for studio_uuid, studio in studio_dicts.items()
        }
