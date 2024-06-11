import typing

from otf.models.responses.classes import OtfClassList

if typing.TYPE_CHECKING:
    from otf import Api


class ClassesApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid

    async def get_classes(
        self, studio_uuids: list[str] | None = None, include_home_studio: bool = True
    ) -> OtfClassList:
        """Get the classes for the user.

        Returns a list of classes that are available for the user, based on the studio UUIDs provided. If no studio
        UUIDs are provided, it will default to the user's home studio.

        Args:
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will
            default to the user's home studio only.
            include_home_studio (bool): Whether to include the home studio in the classes. Default is True.

        Returns:
            OtfClassList: The classes for the user.
        """

        if not studio_uuids:
            studio_uuids = [self._api.home_studio_uuid]
        elif include_home_studio and self._api.home_studio_uuid not in studio_uuids:
            studio_uuids.append(self._api.home_studio_uuid)

        path = "/v1/classes"

        params = {"studio_ids": studio_uuids}
        res = await self._api._classes_request("GET", path, params=params)
        return OtfClassList(classes=res["items"])
