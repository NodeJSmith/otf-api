from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Location(OtfItemBase):
    location_id: int = Field(..., alias="locationId")
    location_uuid: str = Field(..., alias="locationUUId")
    studio_id: int = Field(..., alias="studioId")
    mbo_location_id: int = Field(..., alias="mboLocationId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    latitude: float
    longitude: float
    address1: str
    address2: str | None = None
    city: str
    state: str
    phone: str
    postal_code: str = Field(..., alias="postalCode")


class StudioLocation(OtfItemBase):
    bill_to_address: str = Field(..., alias="billToAddress")
    bill_to_address2: str = Field(..., alias="billToAddress2")
    bill_to_city: str = Field(..., alias="billToCity")
    bill_to_state: str = Field(..., alias="billToState")
    bill_to_postal_code: str = Field(..., alias="billToPostalCode")
    bill_to_region: str = Field(..., alias="billToRegion")
    bill_to_country_id: int = Field(..., alias="billToCountryId")
    bill_to_country: str = Field(..., alias="billToCountry")
    ship_to_address: str = Field(..., alias="shipToAddress")
    ship_to_address2: str | None = Field(None, alias="shipToAddress2")
    ship_to_city: str = Field(..., alias="shipToCity")
    ship_to_state: str = Field(..., alias="shipToState")
    ship_to_postal_code: str = Field(..., alias="shipToPostalCode")
    ship_to_region: str = Field(..., alias="shipToRegion")
    ship_to_country_id: int = Field(..., alias="shipToCountryId")
    ship_to_country: str = Field(..., alias="shipToCountry")
    physical_address: str = Field(..., alias="physicalAddress")
    physical_address2: str | None = Field(None, alias="physicalAddress2")
    physical_city: str = Field(..., alias="physicalCity")
    physical_state: str = Field(..., alias="physicalState")
    physical_postal_code: str = Field(..., alias="physicalPostalCode")
    physical_region: str = Field(..., alias="physicalRegion")
    physical_country_id: int = Field(..., alias="physicalCountryId")
    physical_country: str = Field(..., alias="physicalCountry")
    phone_number: str = Field(..., alias="phoneNumber")
    latitude: str
    longitude: str


class FavoriteStudio(OtfItemBase):
    studio_id: int = Field(..., alias="studioId")
    studio_uuid: str = Field(..., alias="studioUUId")
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
    def studio_ids(self) -> list[int]:
        return [studio.studio_id for studio in self.studios]

    @property
    def studio_uuids(self) -> list[str]:
        return [studio.studio_uuid for studio in self.studios]
