from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studio_detail import StudioDetail


class MemberPurchase(OtfItemBase):
    purchase_uuid: str = Field(..., alias="memberPurchaseUUId")
    name: str | None = None
    price: str | None = None
    purchase_date_time: datetime | None = Field(None, alias="memberPurchaseDateTime")
    purchase_type: str | None = Field(None, alias="memberPurchaseType")
    status: str | None = None
    quantity: int | None = None
    studio: StudioDetail = Field(..., exclude=True, repr=False)

    member_fee_id: int | None = Field(None, alias="memberFeeId", exclude=True, repr=False)
    member_id: int | None = Field(..., alias="memberId", exclude=True, repr=False)
    member_membership_id: int | None = Field(None, alias="memberMembershipId", exclude=True, repr=False)
    member_purchase_id: int | None = Field(..., alias="memberPurchaseId", exclude=True, repr=False)
    member_service_id: int | None = Field(None, alias="memberServiceId", exclude=True, repr=False)
    pos_contract_id: int | None = Field(None, alias="posContractId", exclude=True, repr=False)
    pos_description_id: int | None = Field(None, alias="posDescriptionId", exclude=True, repr=False)
    pos_pmt_ref_no: int | None = Field(None, alias="posPmtRefNo", exclude=True, repr=False)
    pos_product_id: int | None = Field(..., alias="posProductId", exclude=True, repr=False)
    pos_sale_id: int | None = Field(..., alias="posSaleId", exclude=True, repr=False)
    studio_id: int | None = Field(..., alias="studioId", exclude=True, repr=False)
