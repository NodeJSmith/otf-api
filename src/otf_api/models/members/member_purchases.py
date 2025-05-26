from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studios import StudioDetail


class MemberPurchase(OtfItemBase):
    purchase_uuid: str = Field(..., validation_alias="memberPurchaseUUId")
    name: str | None = None
    price: str | None = None
    purchase_date_time: datetime | None = Field(None, validation_alias="memberPurchaseDateTime")
    purchase_type: str | None = Field(None, validation_alias="memberPurchaseType")
    status: str | None = None
    quantity: int | None = None
    studio: StudioDetail = Field(..., exclude=True, repr=False)

    member_fee_id: int | None = Field(None, validation_alias="memberFeeId", exclude=True, repr=False)
    member_id: int | None = Field(..., validation_alias="memberId", exclude=True, repr=False)
    member_membership_id: int | None = Field(None, validation_alias="memberMembershipId", exclude=True, repr=False)
    member_purchase_id: int | None = Field(..., validation_alias="memberPurchaseId", exclude=True, repr=False)
    member_service_id: int | None = Field(None, validation_alias="memberServiceId", exclude=True, repr=False)
    pos_contract_id: int | None = Field(None, validation_alias="posContractId", exclude=True, repr=False)
    pos_description_id: int | None = Field(None, validation_alias="posDescriptionId", exclude=True, repr=False)
    pos_pmt_ref_no: int | None = Field(None, validation_alias="posPmtRefNo", exclude=True, repr=False)
    pos_product_id: int | None = Field(..., validation_alias="posProductId", exclude=True, repr=False)
    pos_sale_id: int | None = Field(..., validation_alias="posSaleId", exclude=True, repr=False)
    studio_id: int | None = Field(..., validation_alias="studioId", exclude=True, repr=False)
