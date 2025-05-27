from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class MemberMembership(OtfItemBase):
    payment_date: datetime | None = Field(None, validation_alias="paymentDate")
    active_date: datetime | None = Field(None, validation_alias="activeDate")
    expiration_date: datetime | None = Field(None, validation_alias="expirationDate")
    current: bool | None = None
    count: int | None = None
    remaining: int | None = None
    name: str | None = None
    updated_date: datetime | None = Field(None, validation_alias="updatedDate")
    created_date: datetime | None = Field(None, validation_alias="createdDate")
    is_deleted: bool | None = Field(None, validation_alias="isDeleted")

    member_membership_id: int | None = Field(None, validation_alias="memberMembershipId", exclude=True, repr=False)
    member_membership_uuid: str | None = Field(None, validation_alias="memberMembershipUUId", exclude=True, repr=False)
    membership_id: int | None = Field(None, validation_alias="membershipId", exclude=True, repr=False)
    member_id: int | None = Field(None, validation_alias="memberId", exclude=True, repr=False)
    mbo_description_id: str | None = Field(None, validation_alias="mboDescriptionId", exclude=True, repr=False)
    created_by: str | None = Field(None, validation_alias="createdBy", exclude=True, repr=False)
    updated_by: str | None = Field(None, validation_alias="updatedBy", exclude=True, repr=False)
