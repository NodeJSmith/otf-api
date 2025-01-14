from datetime import date, datetime

from pydantic import Field, field_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.mixins import AddressMixin
from otf_api.models.studio_detail import StudioDetail


class Address(AddressMixin):
    member_address_uuid: str | None = Field(None, alias="memberAddressUUId", exclude=True, repr=False)
    type: str | None = None


class MemberProfile(OtfItemBase):
    unit_of_measure: str | None = Field(None, alias="unitOfMeasure")
    max_hr_type: str | None = Field(None, alias="maxHrType")
    manual_max_hr: int | None = Field(None, alias="manualMaxHr")
    formula_max_hr: int | None = Field(None, alias="formulaMaxHr")
    automated_hr: int | None = Field(None, alias="automatedHr")

    member_profile_uuid: str = Field(..., alias="memberProfileUUId", exclude=True, repr=False)
    member_optin_flow_type_id: int = Field(..., alias="memberOptinFlowTypeId", exclude=True, repr=False)


class MemberClassSummary(OtfItemBase):
    total_classes_booked: int | None = Field(None, alias="totalClassesBooked")
    total_classes_attended: int | None = Field(None, alias="totalClassesAttended")
    total_intro_classes: int | None = Field(None, alias="totalIntro")
    total_ot_live_classes_booked: int | None = Field(None, alias="totalOTLiveClassesBooked")
    total_ot_live_classes_attended: int | None = Field(None, alias="totalOTLiveClassesAttended")
    total_classes_used_hrm: int | None = Field(None, alias="totalClassesUsedHRM")
    total_studios_visited: int | None = Field(None, alias="totalStudiosVisited")
    first_visit_date: date | None = Field(None, alias="firstVisitDate")
    last_class_visited_date: date | None = Field(None, alias="lastClassVisitedDate")
    last_class_booked_date: date | None = Field(None, alias="lastClassBookedDate")

    last_class_studio_visited: int | None = Field(None, alias="lastClassStudioVisited", exclude=True, repr=False)


class MemberDetail(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUUId")
    cognito_id: str = Field(
        ...,
        alias="cognitoId",
        exclude=True,
        repr=False,
        description="Cognito user ID, not necessary for end users. Also on OtfUser object.",
    )

    home_studio: StudioDetail
    profile: MemberProfile = Field(..., alias="memberProfile")
    class_summary: MemberClassSummary | None = Field(None, alias="memberClassSummary")
    addresses: list[Address] | None = None

    studio_display_name: str = Field(
        ..., alias="userName", description="The value that is displayed on tread/rower tablets and OTBeat screens"
    )
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str = Field(..., alias="email")
    phone_number: str = Field(..., alias="phoneNumber")
    birth_day: date = Field(..., alias="birthDay")
    gender: str = Field(..., alias="gender")
    locale: str = Field(..., alias="locale")
    weight: int = Field(..., alias="weight")
    weight_units: str = Field(..., alias="weightMeasure")
    height: int = Field(..., alias="height")
    height_units: str = Field(..., alias="heightMeasure")

    created_date: datetime = Field(..., alias="createdDate")
    updated_date: datetime = Field(..., alias="updatedDate")

    # unused fields

    # mbo fields
    mbo_id: str | None = Field(None, alias="mboId", exclude=True, repr=False, description="MindBody attr")
    mbo_status: str | None = Field(None, alias="mboStatus", exclude=True, repr=False, description="MindBody attr")
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True, repr=False, description="MindBody attr")
    mbo_unique_id: int | None = Field(None, alias="mboUniqueId", exclude=True, repr=False, description="MindBody attr")

    # ids
    created_by: str | None = Field(None, alias="createdBy", exclude=True, repr=False)
    home_studio_id: int | None = Field(
        None, alias="homeStudioId", exclude=True, repr=False, description="Not used by API"
    )
    member_id: int | None = Field(None, alias="memberId", exclude=True, repr=False, description="Not used by API")
    otf_acs_id: str | None = Field(None, alias="otfAcsId", exclude=True, repr=False)
    updated_by: str | None = Field(None, alias="updatedBy", exclude=True, repr=False)

    # unused address/member detail fields
    address_line1: str | None = Field(None, alias="addressLine1", exclude=True, repr=False)
    address_line2: str | None = Field(None, alias="addressLine2", exclude=True, repr=False)
    alternate_emails: None = Field(None, alias="alternateEmails", exclude=True, repr=False)
    cc_last4: str | None = Field(None, alias="ccLast4", exclude=True, repr=False)
    cc_type: str | None = Field(None, alias="ccType", exclude=True, repr=False)
    city: str | None = Field(None, exclude=True, repr=False)
    home_phone: str | None = Field(None, alias="homePhone", exclude=True, repr=False)
    intro_neccessary: bool | None = Field(None, alias="introNeccessary", exclude=True, repr=False)
    is_deleted: bool | None = Field(None, alias="isDeleted", exclude=True, repr=False)
    is_member_verified: bool | None = Field(None, alias="isMemberVerified", exclude=True, repr=False)
    lead_prospect: bool | None = Field(None, alias="leadProspect", exclude=True, repr=False)
    max_hr: int | None = Field(
        None, alias="maxHr", exclude=True, repr=False, description="Also found in member_profile"
    )
    online_signup: None = Field(None, alias="onlineSignup", exclude=True, repr=False)
    phone_type: None = Field(None, alias="phoneType", exclude=True, repr=False)
    postal_code: str | None = Field(None, alias="postalCode", exclude=True, repr=False)
    profile_picture_url: str | None = Field(None, alias="profilePictureUrl", exclude=True, repr=False)
    state: str | None = Field(None, exclude=True, repr=False)
    work_phone: str | None = Field(None, alias="workPhone", exclude=True, repr=False)
    year_imported: int | None = Field(None, alias="yearImported", exclude=True, repr=False)

    @field_validator("birth_day")
    @classmethod
    def validate_birth_day(cls, value: date | str | None, **_kwargs) -> date | None:
        if value is None:
            return value
        if not isinstance(value, date):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value
