from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Country(OtfItemBase):
    country_id: int = Field(..., alias="countryId")
    country_currency_code: str | None = Field(None, alias="countryCurrencyCode")
    country_currency_name: str | None = Field(None, alias="countryCurrencyName")
    currency_alphabetic_code: str | None = Field(None, alias="currencyAlphabeticCode")


class StudioLocation(OtfItemBase):
    physical_address: str | None = Field(None, alias="physicalAddress")
    physical_address2: str | None = Field(None, alias="physicalAddress2")
    physical_city: str | None = Field(None, alias="physicalCity")
    physical_state: str | None = Field(None, alias="physicalState")
    physical_postal_code: str | None = Field(None, alias="physicalPostalCode")
    physical_region: str | None = Field(None, alias="physicalRegion", exclude=True)
    physical_country: str | None = Field(None, alias="physicalCountry", exclude=True)
    country: Country | None = Field(None, exclude=True)
    phone_number: str | None = Field(None, alias="phoneNumber")
    latitude: float | None = Field(None, exclude=True)
    longitude: float | None = Field(None, exclude=True)


class Language(OtfItemBase):
    language_id: None = Field(None, alias="languageId")
    language_code: None = Field(None, alias="languageCode")
    language_name: None = Field(None, alias="languageName")


class StudioLocationLocalized(OtfItemBase):
    language: Language | None = Field(None, exclude=True)
    studio_name: str | None = Field(None, alias="studioName")
    studio_address: str | None = Field(None, alias="studioAddress")


class StudioProfiles(OtfItemBase):
    is_web: bool | None = Field(None, alias="isWeb")
    intro_capacity: int | None = Field(None, alias="introCapacity")
    is_crm: bool | None = Field(None, alias="isCrm")


class SocialMediaLink(OtfItemBase):
    id: str
    language_id: str | None = Field(None, alias="languageId")
    name: str
    value: str


class StudioDetail(OtfItemBase):
    studio_id: int = Field(..., alias="studioId", exclude=True)
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_location_localized: StudioLocationLocalized | None = Field(
        None, alias="studioLocationLocalized", exclude=True
    )
    studio_location: StudioLocation | None = Field(None, alias="studioLocation")
    studio_name: str | None = Field(None, alias="studioName")
    studio_number: str | None = Field(None, alias="studioNumber", exclude=True)
    studio_physical_location_id: int | None = Field(None, alias="studioPhysicalLocationId", exclude=True)
    studio_profiles: StudioProfiles | None = Field(None, alias="studioProfiles", exclude=True)
    studio_status: str | None = Field(None, alias="studioStatus", exclude=True)
    studio_token: str | None = Field(None, alias="studioToken", exclude=True)
    studio_type_id: int | None = Field(None, alias="studioTypeId", exclude=True)
    studio_version: str | None = Field(None, alias="studioVersion", exclude=True)
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True)
    accepts_ach: bool | None = Field(None, alias="acceptsAch", exclude=True)
    accepts_american_express: bool | None = Field(None, alias="acceptsAmericanExpress", exclude=True)
    accepts_discover: bool | None = Field(None, alias="acceptsDiscover", exclude=True)
    accepts_visa_master_card: bool | None = Field(None, alias="acceptsVisaMasterCard", exclude=True)
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCrWaitlist", exclude=True)
    allows_dashboard_access: bool | None = Field(None, alias="allowsDashboardAccess", exclude=True)
    area_id: int | None = Field(None, alias="areaId", exclude=True)
    commission_percent: int | None = Field(None, alias="commissionPercent", exclude=True)
    contact_email: str | None = Field(None, alias="contactEmail", exclude=True)
    cr_waitlist_flag_last_updated: datetime | None = Field(None, alias="crWaitlistFlagLastUpdated", exclude=True)
    description: str | None = Field(None, exclude=True)
    distance: float | None = Field(None, exclude=True)
    environment: str | None = Field(None, exclude=True)
    is_integrated: bool | None = Field(None, alias="isIntegrated", exclude=True)
    is_mobile: bool | None = Field(None, alias="isMobile", exclude=True)
    is_otbeat: bool | None = Field(None, alias="isOtbeat", exclude=True)
    logo_url: str | None = Field(None, alias="logoUrl", exclude=True)
    market_id: int | None = Field(None, alias="marketId", exclude=True)
    marketing_fund_rate: int | None = Field(None, alias="marketingFundRate", exclude=True)
    open_date: datetime | None = Field(None, alias="openDate", exclude=True)
    pos_type_id: int | None = Field(None, alias="posTypeId", exclude=True)
    pricing_level: str | None = Field(None, alias="pricingLevel", exclude=True)
    re_open_date: datetime | None = Field(None, alias="reOpenDate", exclude=True)
    royalty_rate: int | None = Field(None, alias="royaltyRate", exclude=True)
    sms_package_enabled: bool | None = Field(None, alias="smsPackageEnabled", exclude=True)
    social_media_links: list[SocialMediaLink] | None = Field(None, alias="socialMediaLinks", exclude=True)
    state_id: int | None = Field(None, alias="stateId", exclude=True)
    tax_rate: str | None = Field(None, alias="taxRate", exclude=True)
    time_zone: str | None = Field(None, alias="timeZone", exclude=True)


class Pagination(OtfItemBase):
    page_index: int | None = Field(None, alias="pageIndex")
    page_size: int | None = Field(None, alias="pageSize")
    total_count: int | None = Field(None, alias="totalCount")
    total_pages: int | None = Field(None, alias="totalPages")


class StudioDetailList(OtfItemBase):
    studios: list[StudioDetail]
