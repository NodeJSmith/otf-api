from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.studios import StudioDetail


class MemberPurchase(OtfItemBase):
    """A purchase made by a member, such as a class pack or retail item."""

    purchase_uuid: str = Field(
        ..., validation_alias="memberPurchaseUUId", description="Unique identifier for the purchase."
    )
    name: str | None = Field(None, description="Name of the purchased item or service.")
    price: str | None = Field(None, description="Price of the purchase.")
    purchase_date_time: datetime | None = Field(
        None, validation_alias="memberPurchaseDateTime", description="When the purchase was made."
    )
    purchase_type: str | None = Field(
        None, validation_alias="memberPurchaseType", description="Type of purchase (e.g. class pack, retail)."
    )
    status: str | None = Field(None, description="Current status of the purchase.")
    quantity: int | None = Field(None, description="Number of items purchased.")
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
