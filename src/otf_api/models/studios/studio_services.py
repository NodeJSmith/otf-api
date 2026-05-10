from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studios import StudioDetail


class StudioService(OtfItemBase):
    """A service or class package offered by a studio, such as class packs or memberships."""

    studio: StudioDetail = Field(..., exclude=True, repr=False)
    service_uuid: str = Field(..., validation_alias="serviceUUId", description="Unique identifier for the service.")
    name: str | None = Field(None, description="Name of the service.")
    price: str | None = Field(None, description="Price of the service.")
    qty: int | None = Field(None, description="Quantity included in the service.")
    online_price: str | None = Field(None, validation_alias="onlinePrice", description="Online purchase price.")
    tax_rate: str | None = Field(None, validation_alias="taxRate", description="Tax rate applied to the service.")
    current: bool | None = Field(None, description="Whether the service is currently active.")
    is_deleted: bool | None = Field(
        None, validation_alias="isDeleted", description="Whether the service has been deleted."
    )
    created_date: datetime | None = Field(
        None, validation_alias="createdDate", description="When the service record was created."
    )
    updated_date: datetime | None = Field(
        None, validation_alias="updatedDate", description="When the service record was last updated."
    )

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
