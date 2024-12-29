from datetime import datetime

from inflection import camelize
from pydantic import Field, model_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin


class Location(PhoneLongitudeLatitudeMixin, AddressMixin):
    location_id: int = Field(..., alias="locationId")
    location_uuid: str = Field(..., alias="locationUUId")
    studio_id: int = Field(..., alias="studioId")
    mbo_location_id: int = Field(..., alias="mboLocationId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")


class StudioLocation(PhoneLongitudeLatitudeMixin, AddressMixin):
    studio_location_id: int | None = Field(None, alias="studioLocationId", exclude=True, repr=False)
    billing_address: AddressMixin | None = Field(None, exclude=True, repr=False)
    shipping_address: AddressMixin | None = Field(None, exclude=True, repr=False)

    @model_validator(mode="before")
    @classmethod
    def handle_addresses(cls, values):
        for prefix, field in [("billTo", "billing_address"), ("shipTo", "shipping_address")]:
            address_values = {k.replace(prefix, ""): v for k, v in values.items() if k.startswith(prefix)}
            address_values = {camelize(k, uppercase_first_letter=False): v for k, v in address_values.items()}
            values[field] = AddressMixin(**address_values)

        return values


class FavoriteStudio(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId", description="The studio UUID, used by API")
    studio_id: int = Field(..., alias="studioId", description="Not used by API", exclude=True, repr=False)
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_name: str = Field(..., alias="studioName")
    area_id: int | None = Field(None, alias="areaId")
    market_id: int | None = Field(None, alias="marketId")
    state_id: int | None = Field(None, alias="stateId")
    studio_physical_location_id: int = Field(..., alias="studioPhysicalLocationId")
    studio_number: str = Field(..., alias="studioNumber")
    description: str | None = None
    studio_version: str | None = Field(None, alias="studioVersion")
    studio_token: str = Field(..., alias="studioToken")
    studio_status: str = Field(..., alias="studioStatus")
    open_date: datetime = Field(..., alias="openDate")
    studio_type_id: int = Field(..., alias="studioTypeId")
    pos_type_id: int | None = Field(None, alias="posTypeId")
    logo_url: str | None = Field(None, alias="logoUrl")
    page_color1: str | None = Field(None, alias="pageColor1")
    page_color2: str | None = Field(None, alias="pageColor2")
    page_color3: str | None = Field(None, alias="pageColor3")
    page_color4: str | None = Field(None, alias="pageColor4")
    accepts_visa_master_card: bool = Field(..., alias="acceptsVisaMasterCard")
    accepts_american_express: bool = Field(..., alias="acceptsAmericanExpress")
    accepts_discover: bool = Field(..., alias="acceptsDiscover")
    accepts_ach: bool = Field(..., alias="acceptsACH")
    sms_package_enabled: bool | None = Field(None, alias="smsPackageEnabled")
    allows_dashboard_access: bool | None = Field(None, alias="allowsDashboardAccess")
    pricing_level: str | None = Field(None, alias="pricingLevel")
    contact_email: str = Field(..., alias="contactEmail")
    time_zone: str = Field(..., alias="timeZone")
    environment: str
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")
    is_integrated: bool = Field(..., alias="isIntegrated")
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    locations: list[Location]
    studio_location: StudioLocation = Field(..., alias="studioLocation")


class FavoriteStudioList(OtfItemBase):
    studios: list[FavoriteStudio]

    @property
    def studio_uuids(self) -> list[str]:
        return [studio.studio_uuid for studio in self.studios]

    def __iter__(self):
        return iter(self.studios)

    def __len__(self):
        return len(self.studios)

    def __getitem__(self, item) -> FavoriteStudio:
        return self.studios[item]
