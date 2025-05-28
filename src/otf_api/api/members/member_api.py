import typing
from logging import getLogger
from typing import Any

from otf_api import models
from otf_api.api.client import OtfClient

from .member_client import MemberClient

if typing.TYPE_CHECKING:
    from otf_api import Otf

LOGGER = getLogger(__name__)


class MemberApi:
    def __init__(self, otf: "Otf", otf_client: OtfClient):
        """Initialize the Member API client.

        Args:
            otf (Otf): The OTF API client.
            otf_client (OtfClient): The OTF client to use for requests.
        """
        self.otf = otf
        self.client = MemberClient(otf_client)

    def get_sms_notification_settings(self) -> models.SmsNotificationSettings:
        """Get the member's SMS notification settings.

        Returns:
            SmsNotificationSettings: The member's SMS notification settings.
        """
        res = self.client.get_sms_notification_settings(self.otf.member.phone_number)  # type: ignore

        return models.SmsNotificationSettings(**res)

    def update_sms_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.SmsNotificationSettings:
        """Update the member's SMS notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional SMS notifications.
            transactional_enabled (bool | None): Whether to enable transactional SMS notifications.

        Returns:
            SmsNotificationSettings: The updated SMS notification settings.
        """
        current_settings = self.get_sms_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_sms_opt_in
        )
        transactional_enabled = (
            transactional_enabled if transactional_enabled is not None else current_settings.is_transactional_sms_opt_in
        )

        self.client.post_sms_notification_settings(
            self.otf.member.phone_number,  # type: ignore
            promotional_enabled,  # type: ignore
            transactional_enabled,  # type: ignore
        )

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_sms_notification_settings()
        return new_settings

    def get_email_notification_settings(self) -> models.EmailNotificationSettings:
        """Get the member's email notification settings.

        Returns:
            EmailNotificationSettings: The member's email notification settings.
        """
        res = self.client.get_email_notification_settings(self.otf.member.email)  # type: ignore

        return models.EmailNotificationSettings(**res)

    def update_email_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.EmailNotificationSettings:
        """Update the member's email notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional email notifications.
            transactional_enabled (bool | None): Whether to enable transactional email notifications.

        Returns:
            EmailNotificationSettings: The updated email notification settings.
        """
        current_settings = self.get_email_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_email_opt_in
        )
        transactional_enabled = (
            transactional_enabled
            if transactional_enabled is not None
            else current_settings.is_transactional_email_opt_in
        )

        self.client.post_email_notification_settings(
            self.otf.member.email,  # type: ignore
            promotional_enabled,  # type: ignore
            transactional_enabled,  # type: ignore
        )

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_email_notification_settings()
        return new_settings

    def update_member_name(self, first_name: str | None = None, last_name: str | None = None) -> models.MemberDetail:
        """Update the member's name. Will return the original member details if no names are provided.

        Args:
            first_name (str | None): The first name to update to. Default is None.
            last_name (str | None): The last name to update to. Default is None.

        Returns:
            MemberDetail: The updated member details or the original member details if no changes were made.
        """
        if not first_name and not last_name:
            LOGGER.warning("No names provided, nothing to update.")
            return self.otf.member

        first_name = first_name or self.otf.member.first_name
        last_name = last_name or self.otf.member.last_name

        if first_name == self.otf.member.first_name and last_name == self.otf.member.last_name:
            LOGGER.warning("No changes to names, nothing to update.")
            return self.otf.member

        assert first_name is not None, "First name is required"
        assert last_name is not None, "Last name is required"

        res = self.client.put_member_name(first_name, last_name)

        return models.MemberDetail.create(**res, api=self.otf)

    def get_member_detail(self) -> models.MemberDetail:
        """Get the member details.

        Returns:
            MemberDetail: The member details.
        """
        data = self.client.get_member_detail()

        # use standard StudioDetail model instead of the one returned by this endpoint
        home_studio_uuid = data["homeStudio"]["studioUUId"]
        data["home_studio"] = self.otf.studios.get_studio_detail(home_studio_uuid)

        return models.MemberDetail.create(**data, api=self.otf)

    def get_member_membership(self) -> models.MemberMembership:
        """Get the member's membership details.

        Returns:
            MemberMembership: The member's membership details.
        """
        data = self.client.get_member_membership()
        return models.MemberMembership(**data)

    def get_member_purchases(self) -> list[models.MemberPurchase]:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            list[MemberPurchase]: The member's purchases.
        """
        purchases = self.client.get_member_purchases()

        for p in purchases:
            p["studio"] = self.otf.studios.get_studio_detail(p["studio"]["studioUUId"])

        return [models.MemberPurchase(**purchase) for purchase in purchases]

    # the below do not return any data for me, so I can't test them

    def _get_member_services(self, active_only: bool = True) -> Any:  # noqa: ANN401
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's services.
        """
        data = self.client.get_member_services(active_only)
        return data
