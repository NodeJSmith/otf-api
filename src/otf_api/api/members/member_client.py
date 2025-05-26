from typing import Any

from otf_api.api.client import CACHE, OtfClient


class MemberClient:
    """Client for retrieving and managing member data in the OTF API.

    This class provides methods to access member details, membership information, notification settings,
    and member services. It also allows updating member information such as name and notification preferences.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    @CACHE.memoize(expire=600, tag="member_detail", ignore=(0,))
    def get_member_detail(self) -> dict:
        """Retrieve raw member details."""
        return self.client.default_request(
            "GET", f"/member/members/{self.member_uuid}", params={"include": "memberAddresses,memberClassSummary"}
        )["data"]

    def get_member_membership(self) -> dict:
        """Retrieve raw member membership details."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/memberships")["data"]

    def get_sms_notification_settings(self, phone_number: str) -> dict:
        """Retrieve raw SMS notification settings."""
        return self.client.default_request("GET", path="/sms/v1/preferences", params={"phoneNumber": phone_number})[
            "data"
        ]

    def get_email_notification_settings(self, email: str) -> dict:
        """Retrieve raw email notification settings."""
        return self.client.default_request("GET", path="/otfmailing/v2/preferences", params={"email": email})["data"]

    def get_member_services(self, active_only: bool) -> dict:
        """Retrieve raw member services data."""
        return self.client.default_request(
            "GET", f"/member/members/{self.member_uuid}/services", params={"activeOnly": str(active_only).lower()}
        )

    def get_member_purchases(self) -> dict:
        """Retrieve raw member purchases data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/purchases")["data"]

    def post_sms_notification_settings(
        self, phone_number: str, promotional_enabled: bool, transactional_enabled: bool
    ) -> dict:
        """Retrieve raw response from updating SMS notification settings.

        Warning:
            This endpoint seems to accept almost anything, converting values to truthy/falsey and
            updating the settings accordingly. The one error I've gotten is with -1

            ```
            ERROR - Response:
            {
            "code": "ER_WARN_DATA_OUT_OF_RANGE",
            "message": "An unexpected server error occurred, please try again.",
            "details": [
                    {
                "message": "ER_WARN_DATA_OUT_OF_RANGE: Out of range value for column 'IsPromotionalSMSOptIn' at row 1",
                "additionalInfo": ""
                    }
                ]
            }
            ```
        """
        return self.client.default_request(
            "POST",
            "/sms/v1/preferences",
            json={
                "promosms": promotional_enabled,
                "source": "OTF",
                "transactionalsms": transactional_enabled,
                "phoneNumber": phone_number,
            },
        )

    def post_email_notification_settings(
        self, email: str, promotional_enabled: bool, transactional_enabled: bool
    ) -> dict:
        """Retrieve raw response from updating email notification settings."""
        return self.client.default_request(
            "POST",
            "/otfmailing/v2/preferences",
            json={
                "promotionalEmail": promotional_enabled,
                "source": "OTF",
                "transactionalEmail": transactional_enabled,
                "email": email,
            },
        )

    def put_member_name(self, first_name: str, last_name: str) -> dict:
        """Retrieve raw response from updating member name."""
        CACHE.evict(tag="member_detail", retry=True)
        return self.client.default_request(
            "PUT",
            f"/member/members/{self.member_uuid}",
            json={"firstName": first_name, "lastName": last_name},
        )["data"]

    def get_app_config(self) -> dict[str, Any]:
        """Retrieve raw app configuration data.

        Returns:
            dict[str, Any]: A dictionary containing app configuration data.
        """
        return self.client.default_request("GET", "/member/app-configurations", headers={"SIGV4AUTH_REQUIRED": "true"})
