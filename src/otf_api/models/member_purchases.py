from datetime import datetime

from inflection import camelize
from pydantic import AliasPath, Field, model_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin


class Location(PhoneLongitudeLatitudeMixin, AddressMixin):
    phone: str | None = Field(None, alias="phone")


class CountryCurrency(OtfItemBase):
    country_id: int = Field(..., alias="countryId")
    country_code: str = Field(..., alias="countryCode")
    description: str
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    currency_id: int | None = Field(None, alias=AliasPath("defaultCurrency", "currencyId"))
    currency_alphabetic_code: str | None = Field(None, alias=AliasPath("defaultCurrency", "currencyAlphabeticCode"))


class StudioLocation(PhoneLongitudeLatitudeMixin, AddressMixin):
    studio_location_id: int = Field(..., alias="studioLocationId", exclude=True, repr=False)
    billing_address: AddressMixin | None = Field(None, exclude=True, repr=False)
    shipping_address: AddressMixin | None = Field(None, exclude=True, repr=False)
    country_currency: CountryCurrency | None = Field(None, alias="country_currency", exclude=True, repr=False)

    @model_validator(mode="before")
    @classmethod
    def handle_addresses(cls, values):
        for prefix, field in [("billTo", "billing_address"), ("shipTo", "shipping_address")]:
            address_values = {k.replace(prefix, ""): v for k, v in values.items() if k.startswith(prefix)}
            address_values = {camelize(k, uppercase_first_letter=False): v for k, v in address_values.items()}
            values[field] = AddressMixin(**address_values)

        return values


class Studio(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId", description="The studio UUID, used by API")
    studio_id: int | None = Field(None, alias="studioId", description="Not used by API", exclude=True, repr=False)
    mbo_studio_id: int | None = Field(
        None,
        alias="mboStudioId",
        description="The studio ID used by MindBody, not used by API",
        exclude=True,
        repr=False,
    )
    studio_name: str | None = Field(None, alias="studioName")
    area_id: int | None = Field(None, alias="areaId", exclude=True, repr=False)
    market_id: int | None = Field(None, alias="marketId", exclude=True, repr=False)
    state_id: int | None = Field(None, alias="stateId", exclude=True, repr=False)
    studio_physical_location_id: int | None = Field(None, alias="studioPhysicalLocationId", exclude=True, repr=False)
    studio_number: str | None = Field(None, alias="studioNumber", description="Unused by API", exclude=True, repr=False)
    description: str | None = Field(None, exclude=True, repr=False)
    studio_version: str | None = Field(None, alias="studioVersion", exclude=True, repr=False)
    studio_token: str | None = Field(None, alias="studioToken", exclude=True, repr=False)
    studio_status: str | None = Field(None, alias="studioStatus", exclude=True, repr=False)
    open_date: datetime | None = Field(None, alias="openDate", exclude=True, repr=False)
    studio_type_id: int | None = Field(None, alias="studioTypeId", exclude=True, repr=False)
    pos_type_id: int | None = Field(None, alias="posTypeId", exclude=True, repr=False)
    tax_inclusive_pricing: bool | None = Field(None, alias="taxInclusivePricing", exclude=True, repr=False)
    tax_rate: str | None = Field(None, alias="taxRate", exclude=True, repr=False)
    logo_url: str | None = Field(None, alias="logoUrl", exclude=True, repr=False)
    page_color1: str | None = Field(None, alias="pageColor1", exclude=True, repr=False)
    page_color2: str | None = Field(None, alias="pageColor2", exclude=True, repr=False)
    page_color3: str | None = Field(None, alias="pageColor3", exclude=True, repr=False)
    page_color4: str | None = Field(None, alias="pageColor4", exclude=True, repr=False)
    accepts_visa_master_card: bool | None = Field(None, alias="acceptsVisaMasterCard", exclude=True, repr=False)
    accepts_american_express: bool | None = Field(None, alias="acceptsAmericanExpress", exclude=True, repr=False)
    accepts_discover: bool | None = Field(None, alias="acceptsDiscover", exclude=True, repr=False)
    accepts_ach: bool | None = Field(None, alias="acceptsACH", exclude=True, repr=False)
    sms_package_enabled: bool | None = Field(None, alias="smsPackageEnabled", exclude=True, repr=False)
    allows_dashboard_access: bool | None = Field(None, alias="allowsDashboardAccess", exclude=True, repr=False)
    pricing_level: str | None = Field(None, alias="pricingLevel", exclude=True, repr=False)
    contact_email: str | None = Field(None, alias="contactEmail", exclude=True, repr=False)
    royalty_rate: str | None = Field(None, alias="royaltyRate", exclude=True, repr=False)
    commission_percent: str | None = Field(None, alias="commissionPercent", exclude=True, repr=False)
    marketing_fund_rate: str | None = Field(None, alias="marketingFundRate", exclude=True, repr=False)
    time_zone: str | None = Field(None, alias="timeZone", exclude=True, repr=False)
    environment: str | None = Field(None, exclude=True, repr=False)
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist", exclude=True, repr=False)
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated", exclude=True, repr=False)
    is_integrated: bool = Field(..., alias="isIntegrated", exclude=True, repr=False)
    locations: list[Location] = Field(..., exclude=True, repr=False)
    studio_location: StudioLocation = Field(..., alias="studioLocation")


class MemberPurchase(OtfItemBase):
    member_purchase_id: int = Field(..., alias="memberPurchaseId")
    member_purchase_uuid: str = Field(..., alias="memberPurchaseUUId")
    studio_id: int = Field(..., alias="studioId", description="Unused by API", exclude=True, repr=False)
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


# class MemberPurchaseList(OtfItemBase):
#     data: list[MemberPurchase]

#     def __iter__(self):
#         return iter(self.data)

#     def __len__(self):
#         return len(self.data)

#     def __getitem__(self, item) -> MemberPurchase:
#         return self.data[item]
