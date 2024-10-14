from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Location(OtfItemBase):
    phone: str
    latitude: str
    longitude: str
    address1: str
    address2: str | None = None
    city: str
    state: str
    postal_code: str = Field(..., alias="postalCode")


class Currency(OtfItemBase):
    currency_alphabetic_code: str = Field(..., alias="currencyAlphabeticCode")


class DefaultCurrency(OtfItemBase):
    currency_id: int = Field(..., alias="currencyId")
    currency: Currency


class Country(OtfItemBase):
    country_id: int = Field(..., alias="countryId")
    country_code: str = Field(..., alias="countryCode")
    description: str
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    default_currency: DefaultCurrency = Field(..., alias="defaultCurrency")


class StudioLocation(OtfItemBase):
    studio_location_id: int = Field(..., alias="studioLocationId")
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
    country: Country


class Studio(OtfItemBase):
    studio_id: int = Field(..., alias="studioId")
    studio_uuid: str = Field(..., alias="studioUUId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_name: str = Field(..., alias="studioName")
    area_id: int = Field(..., alias="areaId")
    market_id: int = Field(..., alias="marketId")
    state_id: int = Field(..., alias="stateId")
    studio_physical_location_id: int = Field(..., alias="studioPhysicalLocationId")
    studio_number: str = Field(..., alias="studioNumber")
    description: str
    studio_version: str = Field(..., alias="studioVersion")
    studio_token: str = Field(..., alias="studioToken")
    studio_status: str = Field(..., alias="studioStatus")
    open_date: datetime = Field(..., alias="openDate")
    studio_type_id: int = Field(..., alias="studioTypeId")
    pos_type_id: int = Field(..., alias="posTypeId")
    tax_inclusive_pricing: bool = Field(..., alias="taxInclusivePricing")
    tax_rate: str = Field(..., alias="taxRate")
    logo_url: str = Field(..., alias="logoUrl")
    page_color1: str = Field(..., alias="pageColor1")
    page_color2: str = Field(..., alias="pageColor2")
    page_color3: str = Field(..., alias="pageColor3")
    page_color4: str = Field(..., alias="pageColor4")
    accepts_visa_master_card: bool = Field(..., alias="acceptsVisaMasterCard")
    accepts_american_express: bool = Field(..., alias="acceptsAmericanExpress")
    accepts_discover: bool = Field(..., alias="acceptsDiscover")
    accepts_ach: bool = Field(..., alias="acceptsACH")
    sms_package_enabled: bool = Field(..., alias="smsPackageEnabled")
    allows_dashboard_access: bool = Field(..., alias="allowsDashboardAccess")
    pricing_level: str = Field(..., alias="pricingLevel")
    contact_email: str = Field(..., alias="contactEmail")
    royalty_rate: str = Field(..., alias="royaltyRate")
    commission_percent: str = Field(..., alias="commissionPercent")
    marketing_fund_rate: str = Field(..., alias="marketingFundRate")
    time_zone: str = Field(..., alias="timeZone")
    environment: str
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")
    is_integrated: bool = Field(..., alias="isIntegrated")
    locations: list[Location]
    studio_location: StudioLocation = Field(..., alias="studioLocation")


class MemberPurchase(OtfItemBase):
    member_purchase_id: int = Field(..., alias="memberPurchaseId")
    member_purchase_uuid: str = Field(..., alias="memberPurchaseUUId")
    studio_id: int = Field(..., alias="studioId")
    name: str
    price: str
    member_purchase_date_time: datetime = Field(..., alias="memberPurchaseDateTime")
    member_purchase_type: str = Field(..., alias="memberPurchaseType")
    status: str
    member_service_id: int | None = Field(None, alias="memberServiceId")
    member_membership_id: int | None = Field(None, alias="memberMembershipId")
    member_fee_id: int | None = Field(None, alias="memberFeeId")
    pos_contract_id: int | None = Field(None, alias="posContractId")
    pos_product_id: int = Field(..., alias="posProductId")
    pos_description_id: int | None = Field(None, alias="posDescriptionId")
    pos_pmt_ref_no: int | None = Field(None, alias="posPmtRefNo")
    pos_sale_id: int = Field(..., alias="posSaleId")
    quantity: int
    member_id: int = Field(..., alias="memberId")
    studio: Studio


class MemberPurchaseList(OtfItemBase):
    data: list[MemberPurchase]
