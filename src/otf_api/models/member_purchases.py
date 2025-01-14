from datetime import datetime

from inflection import camelize
from pydantic import AliasPath, Field, model_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin
from otf_api.models.studio_detail import StudioDetail


class MemberPurchase(OtfItemBase):
    purchase_uuid: str = Field(..., alias="memberPurchaseUUId")
    name: str
    price: str
    purchase_date_time: datetime = Field(..., alias="memberPurchaseDateTime")
    purchase_type: str = Field(..., alias="memberPurchaseType")
    status: str
    quantity: int
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


# class MemberPurchaseList(OtfItemBase):
#     data: list[MemberPurchase]

#     def __iter__(self):
#         return iter(self.data)

#     def __len__(self):
#         return len(self.data)

#     def __getitem__(self, item) -> MemberPurchase:
#         return self.data[item]
