from datetime import date, datetime

from pydantic import Field, field_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin, ApiMixin
from otf_api.models.studios.studio_detail import StudioDetail


class Address(AddressMixin, OtfItemBase):
    member_address_uuid: str | None = Field(None, validation_alias="memberAddressUUId", exclude=True, repr=False)
    type: str | None = None


class MemberProfile(OtfItemBase):
    unit_of_measure: str | None = Field(None, validation_alias="unitOfMeasure")
    max_hr_type: str | None = Field(None, validation_alias="maxHrType")
    manual_max_hr: int | None = Field(None, validation_alias="manualMaxHr")
    formula_max_hr: int | None = Field(None, validation_alias="formulaMaxHr")
    automated_hr: int | None = Field(None, validation_alias="automatedHr")

    member_profile_uuid: str | None = Field(None, validation_alias="memberProfileUUId", exclude=True, repr=False)
    member_optin_flow_type_id: int | None = Field(
        None, validation_alias="memberOptinFlowTypeId", exclude=True, repr=False
    )


class MemberClassSummary(OtfItemBase):
    total_classes_booked: int | None = Field(None, validation_alias="totalClassesBooked")
    total_classes_attended: int | None = Field(None, validation_alias="totalClassesAttended")
    total_intro_classes: int | None = Field(None, validation_alias="totalIntro")
    total_ot_live_classes_booked: int | None = Field(None, validation_alias="totalOTLiveClassesBooked")
    total_ot_live_classes_attended: int | None = Field(None, validation_alias="totalOTLiveClassesAttended")
    total_classes_used_hrm: int | None = Field(None, validation_alias="totalClassesUsedHRM")
    total_studios_visited: int | None = Field(None, validation_alias="totalStudiosVisited")
    first_visit_date: date | None = Field(None, validation_alias="firstVisitDate")
    last_class_visited_date: date | None = Field(None, validation_alias="lastClassVisitedDate")
    last_class_booked_date: date | None = Field(None, validation_alias="lastClassBookedDate")

    last_class_studio_visited: int | None = Field(
        None, validation_alias="lastClassStudioVisited", exclude=True, repr=False
    )


class MemberDetail(ApiMixin, OtfItemBase):
    member_uuid: str = Field(..., validation_alias="memberUUId")
    cognito_id: str = Field(
        ...,
        validation_alias="cognitoId",
        exclude=True,
        repr=False,
        description="Cognito user ID, not necessary for end users. Also on OtfUser object.",
    )

    home_studio: StudioDetail
    profile: MemberProfile = Field(..., validation_alias="memberProfile")
    class_summary: MemberClassSummary | None = Field(None, validation_alias="memberClassSummary")
    addresses: list[Address] | None = Field(default_factory=list)

    studio_display_name: str | None = Field(
        None,
        validation_alias="userName",
        description="The value that is displayed on tread/rower tablets and OTBeat screens",
    )
    first_name: str | None = Field(None, validation_alias="firstName")
    last_name: str | None = Field(None, validation_alias="lastName")
    email: str | None = Field(None, validation_alias="email")
    phone_number: str | None = Field(None, validation_alias="phoneNumber")
    birth_day: date | None = Field(None, validation_alias="birthDay")
    gender: str | None = Field(None, validation_alias="gender")
    locale: str | None = Field(None, validation_alias="locale")
    weight: int | None = Field(None, validation_alias="weight")
    weight_units: str | None = Field(None, validation_alias="weightMeasure")
    height: int | None = Field(None, validation_alias="height")
    height_units: str | None = Field(None, validation_alias="heightMeasure")

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
