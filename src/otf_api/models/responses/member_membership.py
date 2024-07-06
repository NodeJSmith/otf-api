from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class MemberMembership(OtfItemBase):
    member_membership_id: int = Field(..., alias="memberMembershipId")
    member_membership_uuid: str = Field(..., alias="memberMembershipUUId")
    membership_id: int = Field(..., alias="membershipId")
    member_id: int = Field(..., alias="memberId")
    payment_date: datetime = Field(..., alias="paymentDate")
    active_date: datetime = Field(..., alias="activeDate")
    expiration_date: datetime = Field(..., alias="expirationDate")
    mbo_description_id: str = Field(..., alias="mboDescriptionId")
    current: bool
    count: int
    remaining: int
    name: str
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_by: str = Field(..., alias="updatedBy")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
