from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studios import StudioDetail


class StudioService(OtfItemBase):
    studio: StudioDetail = Field(..., exclude=True, repr=False)
    service_uuid: str = Field(..., validation_alias="serviceUUId")
    name: str | None = None
    price: str | None = None
    qty: int | None = None
    online_price: str | None = Field(None, validation_alias="onlinePrice")
    tax_rate: str | None = Field(None, validation_alias="taxRate")
    current: bool | None = None
    is_deleted: bool | None = Field(None, validation_alias="isDeleted")
    created_date: datetime | None = Field(None, validation_alias="createdDate")
    updated_date: datetime | None = Field(None, validation_alias="updatedDate")

    # unused fields

    # ids
    mbo_program_id: int | None = Field(None, validation_alias="mboProgramId", exclude=True, repr=False)
    mbo_description_id: str | None = Field(None, validation_alias="mboDescriptionId", exclude=True, repr=False)
    mbo_product_id: int | None = Field(None, validation_alias="mboProductId", exclude=True, repr=False)
    service_id: int | None = Field(None, validation_alias="serviceId", exclude=True, repr=False)
    studio_id: int | None = Field(None, validation_alias="studioId", exclude=True, repr=False)
    created_by: str | None = Field(None, validation_alias="createdBy", exclude=True, repr=False)
    updated_by: str | None = Field(None, validation_alias="updatedBy", exclude=True, repr=False)

    # flags
    is_web: bool | None = Field(None, validation_alias="isWeb", exclude=True, repr=False)
    is_crm: bool | None = Field(None, validation_alias="isCrm", exclude=True, repr=False)
    is_mobile: bool | None = Field(None, validation_alias="isMobile", exclude=True, repr=False)
