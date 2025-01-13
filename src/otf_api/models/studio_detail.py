from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin


class CountryCurrency(OtfItemBase):
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    currency_id: int | None = Field(None, alias=AliasPath("defaultCurrency", "currencyId"))
    currency_alphabetic_code: str | None = Field(None, alias=AliasPath("defaultCurrency", "currencyAlphabeticCode"))


class StudioLocation(PhoneLongitudeLatitudeMixin, AddressMixin):
    physical_region: str | None = Field(None, alias="physicalRegion", exclude=True, repr=False)
    physical_country_id: int | None = Field(None, alias="physicalCountryId", exclude=True, repr=False)
    country_currency: CountryCurrency | None = Field(None, alias="country_currency", exclude=True, repr=False)


class StudioDetail(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId", description="The OTF studio UUID")

    contact_email: str | None = Field(None, alias="contactEmail")
    distance: float | None = Field(
        None, description="Appears to be distance from member or potentially member's home studio"
    )
    studio_location: StudioLocation | None = Field(None, alias="studioLocation")
    studio_name: str | None = Field(None, alias="studioName")
    studio_status: str | None = Field(None, alias="studioStatus", description="Active, Temporarily Closed, Coming Soon")
    time_zone: str | None = Field(None, alias="timeZone")

    # flags
    accepts_ach: bool | None = Field(None, alias="acceptsAch", exclude=True)
    accepts_american_express: bool | None = Field(None, alias="acceptsAmericanExpress", exclude=True)
    accepts_discover: bool | None = Field(None, alias="acceptsDiscover", exclude=True)
    accepts_visa_master_card: bool | None = Field(None, alias="acceptsVisaMasterCard", exclude=True)
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCrWaitlist", exclude=True)
    allows_dashboard_access: bool | None = Field(None, alias="allowsDashboardAccess", exclude=True)
    is_crm: bool | None = Field(None, alias=AliasPath("studioProfiles", "isCrm"), exclude=True)
    is_integrated: bool | None = Field(None, alias="isIntegrated", exclude=True, description="Always 'True'")
    is_mobile: bool | None = Field(None, alias="isMobile", exclude=True)
    is_otbeat: bool | None = Field(None, alias="isOtbeat", exclude=True)
    is_web: bool | None = Field(None, alias=AliasPath("studioProfiles", "isWeb"), exclude=True)
    sms_package_enabled: bool | None = Field(None, alias="smsPackageEnabled", exclude=True)

    # misc
    studio_id: int | None = Field(None, alias="studioId", description="Not used by API")
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True, description="MindBody attr")
    open_date: datetime | None = Field(None, alias="openDate", exclude=True)
    pricing_level: str | None = Field(
        None, alias="pricingLevel", exclude=True, description="Pro, Legacy, Accelerate, or empty"
    )
    re_open_date: datetime | None = Field(None, alias="reOpenDate", exclude=True)
    studio_number: str | None = Field(None, alias="studioNumber", exclude=True)
    studio_physical_location_id: int | None = Field(None, alias="studioPhysicalLocationId", exclude=True)
    studio_token: str | None = Field(None, alias="studioToken", exclude=True)
    studio_type_id: int | None = Field(None, alias="studioTypeId", exclude=True)


class Pagination(OtfItemBase):
    page_index: int | None = Field(None, alias="pageIndex")
    page_size: int | None = Field(None, alias="pageSize")
    total_count: int | None = Field(None, alias="totalCount")
    total_pages: int | None = Field(None, alias="totalPages")


class StudioDetailList(OtfItemBase):
    studios: list[StudioDetail]

    def __len__(self) -> int:
        return len(self.studios)

    def __iter__(self):
        return iter(self.studios)

    def __getitem__(self, item) -> StudioDetail:
        return self.studios[item]
