from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studio_detail import StudioDetail


class StudioService(OtfItemBase):
    studio: StudioDetail = Field(..., exclude=True, repr=False)
    service_uuid: str = Field(..., alias="serviceUUId")
    name: str | None = None
    price: str | None = None
    qty: int | None = None
    online_price: str | None = Field(None, alias="onlinePrice")
    tax_rate: str | None = Field(None, alias="taxRate")
    current: bool | None = None
    is_deleted: bool | None = Field(None, alias="isDeleted")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_date: datetime | None = Field(None, alias="updatedDate")

    # unused fields

    # ids
    mbo_program_id: int | None = Field(None, alias="mboProgramId", exclude=True, repr=False)
    mbo_description_id: str | None = Field(None, alias="mboDescriptionId", exclude=True, repr=False)
    mbo_product_id: int | None = Field(None, alias="mboProductId", exclude=True, repr=False)
    service_id: int | None = Field(None, alias="serviceId", exclude=True, repr=False)
    studio_id: int | None = Field(None, alias="studioId", exclude=True, repr=False)
    created_by: str | None = Field(None, alias="createdBy", exclude=True, repr=False)
    updated_by: str | None = Field(None, alias="updatedBy", exclude=True, repr=False)

    # flags
    is_web: bool | None = Field(None, alias="isWeb", exclude=True, repr=False)
    is_crm: bool | None = Field(None, alias="isCrm", exclude=True, repr=False)
    is_mobile: bool | None = Field(None, alias="isMobile", exclude=True, repr=False)
