from datetime import date, datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase


class Address(OtfItemBase):
    member_address_uuid: str | None = Field(None, alias="memberAddressUUId")
    type: str
    address1: str
    address2: str | None = None
    suburb: str | None = None
    territory: str
    postal_code: str = Field(..., alias="postalCode")
    country: str

    def __init__(self, **data):
        if "memberaddressUUId" in data:
            data["memberAddressUUId"] = data.pop("memberaddressUUId")

        super().__init__(**data)


class MemberCreditCard(OtfItemBase):
    name_on_card: str = Field(..., alias="nameOnCard")
    cc_type: str = Field(..., alias="ccType")
    cc_last4: str = Field(..., alias="ccLast4")


class PhysicalCountryDetails(OtfItemBase):
    country_code: str = Field(..., alias="countryCode")
    description: str


class StudioLocation(OtfItemBase):
    physical_country_id: int = Field(..., alias="physicalCountryId")
    physical_country_details: PhysicalCountryDetails = Field(..., alias="physicalCountryDetails")


class StudioPartner(OtfItemBase):
    studio_acs_id: str = Field(..., alias="studioAcsId")


class HomeStudio(OtfItemBase):
    studio_id: int = Field(..., alias="studioId")
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_name: str = Field(..., alias="studioName")
    studio_number: str = Field(..., alias="studioNumber")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    time_zone: str = Field(..., alias="timeZone")
    is_integrated: bool = Field(..., alias="isIntegrated")
    studio_status: str = Field(..., alias="studioStatus")
    studio_location: StudioLocation = Field(..., alias="studioLocation")
    studio_partner: StudioPartner = Field(..., alias="studioPartner")


class MemberProfile(OtfItemBase):
    member_profile_uuid: str = Field(..., alias="memberProfileUUId")
    unit_of_measure: str = Field(..., alias="unitOfMeasure")
    max_hr_type: str = Field(..., alias="maxHrType")
    manual_max_hr: int = Field(..., alias="manualMaxHr")
    formula_max_hr: int = Field(..., alias="formulaMaxHr")
    automated_hr: int = Field(..., alias="automatedHr")
    member_optin_flow_type_id: int = Field(..., alias="memberOptinFlowTypeId")


class MemberClassSummary(OtfItemBase):
    total_classes_booked: int = Field(..., alias="totalClassesBooked")
    total_classes_attended: int = Field(..., alias="totalClassesAttended")
    total_intro: int = Field(..., alias="totalIntro")
    total_ot_live_classes_booked: int = Field(..., alias="totalOTLiveClassesBooked")
    total_ot_live_classes_attended: int = Field(..., alias="totalOTLiveClassesAttended")
    total_classes_used_hrm: int = Field(..., alias="totalClassesUsedHRM")
    total_studios_visited: int = Field(..., alias="totalStudiosVisited")
    first_visit_date: datetime = Field(..., alias="firstVisitDate")
    last_class_visited_date: datetime = Field(..., alias="lastClassVisitedDate")
    last_class_booked_date: datetime = Field(..., alias="lastClassBookedDate")
    last_class_studio_visited: int = Field(..., alias="lastClassStudioVisited")


class MemberDetail(OtfItemBase):
    member_id: int = Field(..., alias="memberId")
    member_uuid: str = Field(..., alias="memberUUId")
    cognito_id: str = Field(..., alias="cognitoId")
    home_studio_id: int = Field(..., alias="homeStudioId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    mbo_id: str = Field(..., alias="mboId")
    mbo_unique_id: int = Field(..., alias="mboUniqueId")
    mbo_status: str = Field(..., alias="mboStatus")
    user_name: str = Field(..., alias="userName")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str
    profile_picture_url: None = Field(..., alias="profilePictureUrl")
    alternate_emails: None = Field(..., alias="alternateEmails")
    address_line1: None = Field(..., alias="addressLine1")
    address_line2: None = Field(..., alias="addressLine2")
    city: None
    state: None
    postal_code: None = Field(..., alias="postalCode")
    phone_number: str = Field(..., alias="phoneNumber")
    home_phone: str = Field(..., alias="homePhone")
    work_phone: None = Field(..., alias="workPhone")
    phone_type: None = Field(..., alias="phoneType")
    birth_day: date | str = Field(..., alias="birthDay")
    cc_last4: str = Field(..., alias="ccLast4")
    cc_type: str = Field(..., alias="ccType")
    gender: str
    liability: None
    locale: str
    weight: int
    weight_measure: str = Field(..., alias="weightMeasure")
    height: int
    height_measure: str = Field(..., alias="heightMeasure")
    max_hr: int = Field(..., alias="maxHr")
    intro_neccessary: bool = Field(..., alias="introNeccessary")
    online_signup: None = Field(..., alias="onlineSignup")
    year_imported: int = Field(..., alias="yearImported")
    is_member_verified: bool = Field(..., alias="isMemberVerified")
    lead_prospect: bool = Field(..., alias="leadProspect")
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_by: str = Field(..., alias="updatedBy")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    addresses: list[Address] | None = None
    member_credit_card: MemberCreditCard | None = Field(None, alias="memberCreditCard")
    home_studio: HomeStudio = Field(..., alias="homeStudio")
    member_profile: MemberProfile = Field(..., alias="memberProfile")
    member_referrer: None = Field(..., alias="memberReferrer")
    otf_acs_id: str = Field(..., alias="otfAcsId")
    member_class_summary: MemberClassSummary | None = Field(None, alias="memberClassSummary")

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.birth_day and isinstance(self.birth_day, str):
            self.birth_day = datetime.strptime(self.birth_day, "%Y-%m-%d").date()  # noqa
