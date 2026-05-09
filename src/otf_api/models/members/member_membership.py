from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class MemberMembership(OtfItemBase):
    """A member's OrangeTheory membership plan, including billing and expiration details."""

    payment_date: datetime | None = Field(
        None, validation_alias="paymentDate", description="Next scheduled payment date."
    )
    active_date: datetime | None = Field(
        None, validation_alias="activeDate", description="Date the membership became active."
    )
    expiration_date: datetime | None = Field(
        None, validation_alias="expirationDate", description="Date the membership expires."
    )
    current: bool | None = Field(None, description="Whether this is the member's current active membership.")
    count: int | None = Field(None, description="Total number of sessions included in the membership.")
    remaining: int | None = Field(None, description="Number of sessions remaining.")
    name: str | None = Field(None, description="Name of the membership plan.")
    updated_date: datetime | None = Field(
        None, validation_alias="updatedDate", description="When the membership record was last updated."
    )
    created_date: datetime | None = Field(
        None, validation_alias="createdDate", description="When the membership record was created."
    )
    is_deleted: bool | None = Field(
        None, validation_alias="isDeleted", description="Whether the membership has been deleted."
    )

    member_membership_id: int | None = Field(None, validation_alias="memberMembershipId", exclude=True, repr=False)
    member_membership_uuid: str | None = Field(None, validation_alias="memberMembershipUUId", exclude=True, repr=False)
    membership_id: int | None = Field(None, validation_alias="membershipId", exclude=True, repr=False)
    member_id: int | None = Field(None, validation_alias="memberId", exclude=True, repr=False)
    mbo_description_id: str | None = Field(None, validation_alias="mboDescriptionId", exclude=True, repr=False)
    created_by: str | None = Field(None, validation_alias="createdBy", exclude=True, repr=False)
    updated_by: str | None = Field(None, validation_alias="updatedBy", exclude=True, repr=False)
