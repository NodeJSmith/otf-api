from datetime import date, datetime

from pydantic import Field, field_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, ApiMixin
from otf_api.models.studios.studio_detail import StudioDetail


class Address(AddressMixin, OtfItemBase):
    """A member's physical address."""

    member_address_uuid: str | None = Field(None, validation_alias="memberAddressUUId", exclude=True, repr=False)
    type: str | None = Field(None, description="Address type (e.g. home, work).")


class MemberProfile(OtfItemBase):
    """Heart rate and measurement preferences for a member."""

    unit_of_measure: str | None = Field(
        None, validation_alias="unitOfMeasure", description="Preferred unit of measure (e.g. Imperial, Metric)."
    )
    max_hr_type: str | None = Field(
        None, validation_alias="maxHrType", description="Method used to determine max heart rate."
    )
    manual_max_hr: int | None = Field(
        None, validation_alias="manualMaxHr", description="Manually entered max heart rate."
    )
    formula_max_hr: int | None = Field(
        None, validation_alias="formulaMaxHr", description="Formula-calculated max heart rate."
    )
    automated_hr: int | None = Field(
        None, validation_alias="automatedHr", description="Automatically detected heart rate."
    )

    member_profile_uuid: str | None = Field(None, validation_alias="memberProfileUUId", exclude=True, repr=False)
    member_optin_flow_type_id: int | None = Field(
        None, validation_alias="memberOptinFlowTypeId", exclude=True, repr=False
    )


class MemberClassSummary(OtfItemBase):
    """Aggregate statistics about a member's class attendance history."""

    total_classes_booked: int | None = Field(
        None, validation_alias="totalClassesBooked", description="Total number of classes booked."
    )
    total_classes_attended: int | None = Field(
        None, validation_alias="totalClassesAttended", description="Total number of classes attended."
    )
    total_intro_classes: int | None = Field(
        None, validation_alias="totalIntro", description="Total number of intro classes taken."
    )
    total_ot_live_classes_booked: int | None = Field(
        None, validation_alias="totalOTLiveClassesBooked", description="Total OT Live classes booked."
    )
    total_ot_live_classes_attended: int | None = Field(
        None, validation_alias="totalOTLiveClassesAttended", description="Total OT Live classes attended."
    )
    total_classes_used_hrm: int | None = Field(
        None, validation_alias="totalClassesUsedHRM", description="Total classes where a heart rate monitor was used."
    )
    total_studios_visited: int | None = Field(
        None, validation_alias="totalStudiosVisited", description="Number of unique studios visited."
    )
    first_visit_date: date | None = Field(
        None, validation_alias="firstVisitDate", description="Date of the member's first studio visit."
    )
    last_class_visited_date: date | None = Field(
        None, validation_alias="lastClassVisitedDate", description="Date of the member's most recent class visit."
    )
    last_class_booked_date: date | None = Field(
        None, validation_alias="lastClassBookedDate", description="Date of the member's most recent booking."
    )

    last_class_studio_visited: int | None = Field(
        None, validation_alias="lastClassStudioVisited", exclude=True, repr=False
    )


class MemberDetail(ApiMixin, OtfItemBase):
    """Detailed information about an OrangeTheory member, including profile, address, and class summary."""

    member_uuid: str = Field(..., validation_alias="memberUUId", description="Unique identifier for the member.")
    cognito_id: str = Field(
        ...,
        validation_alias="cognitoId",
        exclude=True,
        repr=False,
        description="Cognito user ID, not necessary for end users. Also on OtfUser object.",
    )

    home_studio: StudioDetail = Field(..., description="The member's home studio.")
    profile: MemberProfile = Field(
        ..., validation_alias="memberProfile", description="Heart rate and measurement preferences."
    )
    class_summary: MemberClassSummary | None = Field(
        None, validation_alias="memberClassSummary", description="Aggregate class attendance statistics."
    )
    addresses: list[Address] | None = Field(default_factory=list, description="List of member addresses.")

    studio_display_name: str | None = Field(
        None,
        validation_alias="userName",
        description="The value that is displayed on tread/rower tablets and OTBeat screens",
    )
    first_name: str | None = Field(None, validation_alias="firstName", description="The member's first name.")
    last_name: str | None = Field(None, validation_alias="lastName", description="The member's last name.")
    email: str | None = Field(None, validation_alias="email", description="The member's email address.")
    phone_number: str | None = Field(None, validation_alias="phoneNumber", description="The member's phone number.")
    birth_day: date | None = Field(None, validation_alias="birthDay", description="The member's date of birth.")
    gender: str | None = Field(None, validation_alias="gender", description="The member's gender.")
    locale: str | None = Field(None, validation_alias="locale", description="The member's locale setting.")
    weight: int | None = Field(None, validation_alias="weight", description="The member's weight.")
    weight_units: str | None = Field(None, validation_alias="weightMeasure", description="Unit of measure for weight.")
    height: int | None = Field(None, validation_alias="height", description="The member's height.")
    height_units: str | None = Field(None, validation_alias="heightMeasure", description="Unit of measure for height.")

    # unused fields - leaving these in for now in case someone finds a purpose for them
    # but they will potentially (likely?) be removed in the future

    # mbo fields
    mbo_id: str | None = Field(None, validation_alias="mboId", exclude=True, repr=False, description="MindBody attr")
    mbo_status: str | None = Field(
        None, validation_alias="mboStatus", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_studio_id: int | None = Field(
        None, validation_alias="mboStudioId", exclude=True, repr=False, description="MindBody attr"
    )
    mbo_unique_id: int | None = Field(
        None, validation_alias="mboUniqueId", exclude=True, repr=False, description="MindBody attr"
    )

    # ids
    created_by: str | None = Field(None, validation_alias="createdBy", exclude=True, repr=False)
    home_studio_id: int | None = Field(
        None, validation_alias="homeStudioId", exclude=True, repr=False, description="Not used by API"
    )
    member_id: int | None = Field(
        None, validation_alias="memberId", exclude=True, repr=False, description="Not used by API"
    )
    otf_acs_id: str | None = Field(None, validation_alias="otfAcsId", exclude=True, repr=False)
    updated_by: str | None = Field(None, validation_alias="updatedBy", exclude=True, repr=False)

    # unused address/member detail fields
    created_date: datetime | None = Field(None, validation_alias="createdDate", exclude=True, repr=False)
    updated_date: datetime | None = Field(None, validation_alias="updatedDate", exclude=True, repr=False)

    address_line1: str | None = Field(None, validation_alias="addressLine1", exclude=True, repr=False)
    address_line2: str | None = Field(None, validation_alias="addressLine2", exclude=True, repr=False)
    alternate_emails: None = Field(None, validation_alias="alternateEmails", exclude=True, repr=False)
    cc_last4: str | None = Field(None, validation_alias="ccLast4", exclude=True, repr=False)
    cc_type: str | None = Field(None, validation_alias="ccType", exclude=True, repr=False)
    city: str | None = Field(None, exclude=True, repr=False)
    home_phone: str | None = Field(None, validation_alias="homePhone", exclude=True, repr=False)
    intro_neccessary: bool | None = Field(None, validation_alias="introNeccessary", exclude=True, repr=False)
    is_deleted: bool | None = Field(None, validation_alias="isDeleted", exclude=True, repr=False)
    is_member_verified: bool | None = Field(None, validation_alias="isMemberVerified", exclude=True, repr=False)
    lead_prospect: bool | None = Field(None, validation_alias="leadProspect", exclude=True, repr=False)
    max_hr: int | None = Field(
        None, validation_alias="maxHr", exclude=True, repr=False, description="Also found in member_profile"
    )
    online_signup: None = Field(None, validation_alias="onlineSignup", exclude=True, repr=False)
    phone_type: None = Field(None, validation_alias="phoneType", exclude=True, repr=False)
    postal_code: str | None = Field(None, validation_alias="postalCode", exclude=True, repr=False)
    state: str | None = Field(None, exclude=True, repr=False)
    work_phone: str | None = Field(None, validation_alias="workPhone", exclude=True, repr=False)
    year_imported: int | None = Field(None, validation_alias="yearImported", exclude=True, repr=False)

    @field_validator("birth_day")
    @classmethod
    def validate_birth_day(cls, value: date | str | None, **_kwargs) -> date | None:
        """Convert birth_day to a date object if it is in the format of YYYY-MM-DD."""
        if value is None:
            return value
        if not isinstance(value, date):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value

    def update_name(self, first_name: str | None = None, last_name: str | None = None) -> None:
        """Update the name of the member.

        Args:
            first_name (str | None): The new first name of the member.
            last_name (str | None): The new last name of the member.
        """
        self.raise_if_api_not_set()

        updated_member = self._api.members.update_member_name(first_name, last_name)
        self.first_name = updated_member.first_name
        self.last_name = updated_member.last_name
