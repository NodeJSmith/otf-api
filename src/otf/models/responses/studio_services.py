from datetime import datetime

from pydantic import BaseModel, Field


class Currency(BaseModel):
    currency_alphabetic_code: str = Field(..., alias="currencyAlphabeticCode")


class DefaultCurrency(BaseModel):
    currency_id: int = Field(..., alias="currencyId")
    currency: Currency


class Country(BaseModel):
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    default_currency: DefaultCurrency = Field(..., alias="defaultCurrency")


class StudioLocation(BaseModel):
    studio_location_id: int = Field(..., alias="studioLocationId")
    country: Country


class Studio(BaseModel):
    studio_id: int = Field(..., alias="studioId")
    studio_location: StudioLocation = Field(..., alias="studioLocation")


class StudioService(BaseModel):
    service_id: int = Field(..., alias="serviceId")
    service_uuid: str = Field(..., alias="serviceUUId")
    studio_id: int = Field(..., alias="studioId")
    name: str
    price: str
    qty: int
    mbo_program_id: int = Field(..., alias="mboProgramId")
    mbo_description_id: str = Field(..., alias="mboDescriptionId")
    mbo_product_id: int = Field(..., alias="mboProductId")
    online_price: str = Field(..., alias="onlinePrice")
    tax_rate: str = Field(..., alias="taxRate")
    current: bool
    is_web: bool = Field(..., alias="isWeb")
    is_crm: bool = Field(..., alias="isCrm")
    is_mobile: bool = Field(..., alias="isMobile")
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_by: str = Field(..., alias="updatedBy")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    studio: Studio


class StudioServiceList(BaseModel):
    data: list[StudioService]
