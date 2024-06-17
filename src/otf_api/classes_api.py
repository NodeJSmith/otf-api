import typing
from datetime import datetime

from otf_api.models.responses.classes import OtfClassList

if typing.TYPE_CHECKING:
    from otf_api import Api


class ClassesApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid

    async def get_classes(
        self,
        studio_uuids: list[str] | None = None,
        include_home_studio: bool = True,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> OtfClassList:
        """Get the classes for the user.

        Returns a list of classes that are available for the user, based on the studio UUIDs provided. If no studio
        UUIDs are provided, it will default to the user's home studio.

        Args:
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will\
            default to the user's home studio only.
            include_home_studio (bool): Whether to include the home studio in the classes. Default is True.
            start_date (str | None): The start date to get classes for, in the format "YYYY-MM-DD". Default is None.
            end_date (str | None): The end date to get classes for, in the format "YYYY-MM-DD". Default is None.
            limit (int | None): Limit the number of classes returned. Default is None.

        Returns:
            OtfClassList: The classes for the user.
        """

        if not studio_uuids:
            studio_uuids = [self._api.home_studio.studio_uuid]
        elif include_home_studio and self._api.home_studio.studio_uuid not in studio_uuids:
            studio_uuids.append(self._api.home_studio.studio_uuid)

        path = "/v1/classes"

        params = {"studio_ids": studio_uuids}
        res = await self._api._classes_request("GET", path, params=params)
        classes_list = OtfClassList(classes=res["items"])

        if start_date:
            start_dtme = datetime.strptime(start_date, "%Y-%m-%d")  # noqa
            classes_list.classes = [c for c in classes_list.classes if c.starts_at_local >= start_dtme]

        if end_date:
            end_dtme = datetime.strptime(end_date, "%Y-%m-%d")  # noqa
            classes_list.classes = [c for c in classes_list.classes if c.ends_at_local <= end_dtme]

        if limit:
            classes_list.classes = classes_list.classes[:limit]

        for otf_class in classes_list.classes:
            otf_class.is_home_studio = otf_class.studio.id == self._api.home_studio.studio_uuid

        return classes_list
