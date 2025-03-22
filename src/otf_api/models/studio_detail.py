from datetime import datetime

from pydantic import AliasChoices, AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import StudioStatus
from otf_api.models.mixins import AddressMixin


class StudioLocation(AddressMixin):
    phone_number: str | None = Field(None, alias=AliasChoices("phone", "phoneNumber"))
    latitude: float | None = Field(None, alias=AliasChoices("latitude"))
    longitude: float | None = Field(None, alias=AliasChoices("longitude"))

    physical_region: str | None = Field(None, alias="physicalRegion", exclude=True, repr=False)
    physical_country_id: int | None = Field(None, alias="physicalCountryId", exclude=True, repr=False)


class StudioDetail(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId", description="The OTF studio UUID")

    contact_email: str | None = Field(None, alias="contactEmail")
    distance: float | None = Field(
        None,
        description="Distance from latitude and longitude provided to `search_studios_by_geo` method,\
              NULL if that method was not used",
        exclude=True,
        repr=False,
    )
    location: StudioLocation = Field(..., alias="studioLocation", default_factory=StudioLocation)
    name: str | None = Field(None, alias="studioName")
    status: StudioStatus | None = Field(
        None, alias="studioStatus", description="Active, Temporarily Closed, Coming Soon"
    )
    time_zone: str | None = Field(None, alias="timeZone")

    # flags
    accepts_ach: bool | None = Field(None, alias="acceptsAch", exclude=True, repr=False)
    accepts_american_express: bool | None = Field(None, alias="acceptsAmericanExpress", exclude=True, repr=False)
    accepts_discover: bool | None = Field(None, alias="acceptsDiscover", exclude=True, repr=False)
    accepts_visa_master_card: bool | None = Field(None, alias="acceptsVisaMasterCard", exclude=True, repr=False)
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCrWaitlist", exclude=True, repr=False)
    allows_dashboard_access: bool | None = Field(None, alias="allowsDashboardAccess", exclude=True, repr=False)
    is_crm: bool | None = Field(None, alias=AliasPath("studioProfiles", "isCrm"), exclude=True, repr=False)
    is_integrated: bool | None = Field(
        None, alias="isIntegrated", exclude=True, repr=False, description="Always 'True'"
    )
    is_mobile: bool | None = Field(None, alias="isMobile", exclude=True, repr=False)
    is_otbeat: bool | None = Field(None, alias="isOtbeat", exclude=True, repr=False)
    is_web: bool | None = Field(None, alias=AliasPath("studioProfiles", "isWeb"), exclude=True, repr=False)
    sms_package_enabled: bool | None = Field(None, alias="smsPackageEnabled", exclude=True, repr=False)

    # misc
    studio_id: int | None = Field(None, alias="studioId", description="Not used by API", exclude=True, repr=False)
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True, repr=False, description="MindBody attr")
    open_date: datetime | None = Field(None, alias="openDate", exclude=True, repr=False)
    pricing_level: str | None = Field(
        None, alias="pricingLevel", exclude=True, repr=False, description="Pro, Legacy, Accelerate, or empty"
    )
    re_open_date: datetime | None = Field(None, alias="reOpenDate", exclude=True, repr=False)
    studio_number: str | None = Field(None, alias="studioNumber", exclude=True, repr=False)
    studio_physical_location_id: int | None = Field(None, alias="studioPhysicalLocationId", exclude=True, repr=False)
    studio_token: str | None = Field(None, alias="studioToken", exclude=True, repr=False)
    studio_type_id: int | None = Field(None, alias="studioTypeId", exclude=True, repr=False)
