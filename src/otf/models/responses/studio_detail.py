from datetime import datetime

from pydantic import BaseModel, Field


class Country(BaseModel):
    country_id: int = Field(..., alias="countryId")
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    country_currency_name: str = Field(..., alias="countryCurrencyName")
    currency_alphabetic_code: str = Field(..., alias="currencyAlphabeticCode")


class StudioLocation(BaseModel):
    physical_address: str = Field(..., alias="physicalAddress")
    physical_address2: str | None = Field(..., alias="physicalAddress2")
    physical_city: str = Field(..., alias="physicalCity")
    physical_state: str = Field(..., alias="physicalState")
    physical_postal_code: str = Field(..., alias="physicalPostalCode")
    physical_region: str = Field(..., alias="physicalRegion")
    physical_country: str = Field(..., alias="physicalCountry")
    country: Country
    phone_number: str = Field(..., alias="phoneNumber")
    latitude: float
    longitude: float


class Language(BaseModel):
    language_id: None = Field(..., alias="languageId")
    language_code: None = Field(..., alias="languageCode")
    language_name: None = Field(..., alias="languageName")


class StudioLocationLocalized(BaseModel):
    language: Language
    studio_name: None = Field(..., alias="studioName")
    studio_address: None = Field(..., alias="studioAddress")


class StudioProfiles(BaseModel):
    is_web: bool = Field(..., alias="isWeb")
    intro_capacity: int = Field(..., alias="introCapacity")
    is_crm: bool | None = Field(..., alias="isCrm")


class SocialMediaLink(BaseModel):
    id: str
    language_id: str = Field(..., alias="languageId")
    name: str
    value: str


class StudioDetail(BaseModel):
    studio_id: int = Field(..., alias="studioId")
    studio_uuid: str = Field(..., alias="studioUUId")
    mbo_studio_id: int | None = Field(..., alias="mboStudioId")
    studio_number: str = Field(..., alias="studioNumber")
    studio_name: str = Field(..., alias="studioName")
    studio_physical_location_id: int = Field(..., alias="studioPhysicalLocationId")
    time_zone: str | None = Field(..., alias="timeZone")
    contact_email: str | None = Field(..., alias="contactEmail")
    studio_token: str = Field(..., alias="studioToken")
    environment: str
    pricing_level: str | None = Field(..., alias="pricingLevel")
    tax_rate: str | None = Field(..., alias="taxRate")
    accepts_visa_master_card: bool = Field(..., alias="acceptsVisaMasterCard")
    accepts_american_express: bool = Field(..., alias="acceptsAmericanExpress")
    accepts_discover: bool = Field(..., alias="acceptsDiscover")
    accepts_ach: bool = Field(..., alias="acceptsAch")
    is_integrated: bool = Field(..., alias="isIntegrated")
    description: str | None = None
    studio_version: str | None = Field(..., alias="studioVersion")
    studio_status: str = Field(..., alias="studioStatus")
    open_date: datetime | None = Field(..., alias="openDate")
    re_open_date: datetime | None = Field(..., alias="reOpenDate")
    studio_type_id: int | None = Field(..., alias="studioTypeId")
    pos_type_id: int | None = Field(..., alias="posTypeId")
    market_id: int | None = Field(..., alias="marketId")
    area_id: int | None = Field(..., alias="areaId")
    state_id: int | None = Field(..., alias="stateId")
    logo_url: str | None = Field(..., alias="logoUrl")
    page_color1: str | None = Field(..., alias="pageColor1")
    page_color2: str | None = Field(..., alias="pageColor2")
    page_color3: str | None = Field(..., alias="pageColor3")
    page_color4: str | None = Field(..., alias="pageColor4")
    sms_package_enabled: bool | None = Field(..., alias="smsPackageEnabled")
    allows_dashboard_access: bool | None = Field(..., alias="allowsDashboardAccess")
    allows_cr_waitlist: bool = Field(..., alias="allowsCrWaitlist")
    cr_waitlist_flag_last_updated: datetime | None = Field(..., alias="crWaitlistFlagLastUpdated")
    royalty_rate: int | None = Field(..., alias="royaltyRate")
    marketing_fund_rate: int | None = Field(..., alias="marketingFundRate")
    commission_percent: int | None = Field(..., alias="commissionPercent")
    is_mobile: bool | None = Field(..., alias="isMobile")
    is_otbeat: bool | None = Field(..., alias="isOtbeat")
    distance: float | None = None
    studio_location: StudioLocation = Field(..., alias="studioLocation")
    studio_location_localized: StudioLocationLocalized = Field(..., alias="studioLocationLocalized")
    studio_profiles: StudioProfiles = Field(..., alias="studioProfiles")
    social_media_links: list[SocialMediaLink] = Field(..., alias="socialMediaLinks")


class Pagination(BaseModel):
    page_index: int = Field(..., alias="pageIndex")
    page_size: int = Field(..., alias="pageSize")
    total_count: int = Field(..., alias="totalCount")
    total_pages: int = Field(..., alias="totalPages")


class StudioDetailList(BaseModel):
    studios: list[StudioDetail]
