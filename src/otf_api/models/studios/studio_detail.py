from datetime import datetime

from pydantic import AliasChoices, AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, ApiMixin

from .enums import StudioStatus


class StudioLocation(AddressMixin, OtfItemBase):
    phone_number: str | None = Field(None, validation_alias=AliasChoices("phone", "phoneNumber"))
    latitude: float | None = Field(None, validation_alias=AliasChoices("latitude"))
    longitude: float | None = Field(None, validation_alias=AliasChoices("longitude"))

    physical_region: str | None = Field(None, validation_alias="physicalRegion", exclude=True, repr=False)
    physical_country_id: int | None = Field(None, validation_alias="physicalCountryId", exclude=True, repr=False)


class StudioDetail(ApiMixin, OtfItemBase):
    studio_uuid: str = Field(..., validation_alias="studioUUId", description="The OTF studio UUID")

    contact_email: str | None = Field(None, validation_alias="contactEmail")
    distance: float | None = Field(
        None,
        description="Distance from latitude and longitude provided to `search_studios_by_geo` method,\
              NULL if that method was not used",
        exclude=True,
        repr=False,
    )
    location: StudioLocation = Field(..., validation_alias="studioLocation", default_factory=StudioLocation)  # type: ignore
    name: str | None = Field(None, validation_alias="studioName")
    status: StudioStatus | None = Field(
        None, validation_alias="studioStatus", description="Active, Temporarily Closed, Coming Soon"
    )
    time_zone: str | None = Field(None, validation_alias="timeZone")

    # flags
    accepts_ach: bool | None = Field(None, validation_alias="acceptsAch", exclude=True, repr=False)
    accepts_american_express: bool | None = Field(
        None, validation_alias="acceptsAmericanExpress", exclude=True, repr=False
    )
    accepts_discover: bool | None = Field(None, validation_alias="acceptsDiscover", exclude=True, repr=False)
    accepts_visa_master_card: bool | None = Field(
        None, validation_alias="acceptsVisaMasterCard", exclude=True, repr=False
    )
    allows_cr_waitlist: bool | None = Field(None, validation_alias="allowsCrWaitlist", exclude=True, repr=False)
    allows_dashboard_access: bool | None = Field(
        None, validation_alias="allowsDashboardAccess", exclude=True, repr=False
    )
    is_crm: bool | None = Field(None, validation_alias=AliasPath("studioProfiles", "isCrm"), exclude=True, repr=False)
    is_integrated: bool | None = Field(
        None, validation_alias="isIntegrated", exclude=True, repr=False, description="Always 'True'"
    )
    is_mobile: bool | None = Field(None, validation_alias="isMobile", exclude=True, repr=False)
    is_otbeat: bool | None = Field(None, validation_alias="isOtbeat", exclude=True, repr=False)
    is_web: bool | None = Field(None, validation_alias=AliasPath("studioProfiles", "isWeb"), exclude=True, repr=False)
    sms_package_enabled: bool | None = Field(None, validation_alias="smsPackageEnabled", exclude=True, repr=False)

    # misc
    studio_id: int | None = Field(
        None, validation_alias="studioId", description="Not used by API", exclude=True, repr=False
    )
    mbo_studio_id: int | None = Field(
        None, validation_alias="mboStudioId", exclude=True, repr=False, description="MindBody attr"
    )
    open_date: datetime | None = Field(None, validation_alias="openDate", exclude=True, repr=False)
    pricing_level: str | None = Field(
        None, validation_alias="pricingLevel", exclude=True, repr=False, description="Pro, Legacy, Accelerate, or empty"
    )
    re_open_date: datetime | None = Field(None, validation_alias="reOpenDate", exclude=True, repr=False)
    studio_number: str | None = Field(None, validation_alias="studioNumber", exclude=True, repr=False)
    studio_physical_location_id: int | None = Field(
        None, validation_alias="studioPhysicalLocationId", exclude=True, repr=False
    )
    studio_token: str | None = Field(None, validation_alias="studioToken", exclude=True, repr=False)
    studio_type_id: int | None = Field(None, validation_alias="studioTypeId", exclude=True, repr=False)

    @classmethod
    def create_empty_model(cls, studio_uuid: str) -> "StudioDetail":
        """Create an empty model with the given studio_uuid."""
        # pylance doesn't know that the rest of the fields default to None, so we use type: ignore
        return StudioDetail(studioUUId=studio_uuid, studioName="Studio Not Found", studioStatus="Unknown")  # type: ignore

    def add_to_favorites(self) -> None:
        """Adds the studio to the user's favorites."""
        self.raise_if_api_not_set()
        self._api.studios.add_favorite_studio(self.studio_uuid)

    def remove_from_favorites(self) -> None:
        """Removes the studio from the user's favorites."""
        self.raise_if_api_not_set()
        self._api.studios.remove_favorite_studio(self.studio_uuid)
