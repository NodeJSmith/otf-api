from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase


class MemberProfile(OtfItemBase):
    is_latest_agreement_signed: bool = Field(..., alias="isLatestAgreementSigned")


class StudioProfiles(OtfItemBase):
    studio_id: int = Field(..., alias="studioId")
    is_franchise_agreement_enabled: int = Field(..., alias="isFranchiseAgreementEnabled")


class HomeStudio(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_name: str = Field(..., alias="studioName")
    description: str
    contact_email: str = Field(..., alias="contactEmail")
    status: str
    logo_url: str = Field(..., alias="logoUrl")
    time_zone: str = Field(..., alias="timeZone")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_id: int = Field(..., alias="studioId")
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")
    studio_profiles: StudioProfiles = Field(..., alias="studioProfiles")


class MemberService(OtfItemBase):
    member_service_id: int = Field(..., alias="memberServiceId")
    member_service_uuid: str = Field(..., alias="memberServiceUUId")
    service_name: str = Field(..., alias="serviceName")
    studio_id: int = Field(..., alias="studioId")
    mbo_client_service_id: int = Field(..., alias="mboClientServiceId")
    current: bool
    member_id: int = Field(..., alias="memberId")
    service_id: int = Field(..., alias="serviceId")
    remaining: int
    count: int
    payment_date: datetime = Field(..., alias="paymentDate")
    expiration_date: datetime = Field(..., alias="expirationDate")
    active_date: datetime = Field(..., alias="activeDate")
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")


class ServiceItem(OtfItemBase):
    service_id: int = Field(..., alias="serviceId")
    name: str
    member_service: MemberService = Field(..., alias="MemberService")


class Member(OtfItemBase):
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
    birth_day: str = Field(..., alias="birthDay")
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
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    member_profile: MemberProfile = Field(..., alias="memberProfile")
    home_studio: HomeStudio = Field(..., alias="homeStudio")
    membership: None
    service: list[ServiceItem]
    notes: str


class Studio(OtfItemBase):
    studio_uuid: str = Field(..., alias="studioUUId")
    studio_name: str = Field(..., alias="studioName")
    description: str
    contact_email: str = Field(..., alias="contactEmail")
    status: str
    logo_url: str = Field(..., alias="logoUrl")
    time_zone: str = Field(..., alias="timeZone")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_id: int = Field(..., alias="studioId")
    allows_cr_waitlist: bool = Field(..., alias="allowsCRWaitlist")
    cr_waitlist_flag_last_updated: datetime = Field(..., alias="crWaitlistFlagLastUpdated")


class Location(OtfItemBase):
    location_id: int = Field(..., alias="locationId")
    location_uuid: str = Field(..., alias="locationUUId")


class Coach(OtfItemBase):
    coach_uuid: str = Field(..., alias="coachUUId")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    mbo_coach_id: int = Field(..., alias="mboCoachId")
    name: str


class Class(OtfItemBase):
    class_id: int = Field(..., alias="classId")
    class_uuid: str = Field(..., alias="classUUId")
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    mbo_class_id: int = Field(..., alias="mboClassId")
    mbo_class_schedule_id: int = Field(..., alias="mboClassScheduleId")
    mbo_program_id: int = Field(..., alias="mboProgramId")
    studio_id: int = Field(..., alias="studioId")
    coach_id: int = Field(..., alias="coachId")
    location_id: int = Field(..., alias="locationId")
    name: str
    description: str
    program_name: str = Field(..., alias="programName")
    program_schedule_type: str = Field(..., alias="programScheduleType")
    program_cancel_offset: int = Field(..., alias="programCancelOffset")
    max_capacity: int = Field(..., alias="maxCapacity")
    total_booked: int = Field(..., alias="totalBooked")
    web_capacity: int = Field(..., alias="webCapacity")
    web_booked: int = Field(..., alias="webBooked")
    total_booked_waitlist: int = Field(..., alias="totalBookedWaitlist")
    start_date_time: datetime = Field(..., alias="startDateTime")
    end_date_time: datetime = Field(..., alias="endDateTime")
    is_cancelled: bool = Field(..., alias="isCancelled")
    substitute: bool
    is_active: bool = Field(..., alias="isActive")
    is_waitlist_available: bool = Field(..., alias="isWaitlistAvailable")
    is_enrolled: bool = Field(..., alias="isEnrolled")
    is_hide_cancel: bool = Field(..., alias="isHideCancel")
    is_available: bool = Field(..., alias="isAvailable")
    room_number: int = Field(..., alias="roomNumber")
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    studio: Studio
    location: Location
    coach: Coach
    attributes: dict[str, Any]


class Class1(OtfItemBase):
    mbo_studio_id: int = Field(..., alias="mboStudioId")
    studio_uuid: str = Field(..., alias="studioUUId")


class CustomData(OtfItemBase):
    otf_class: Class1 = Field(..., alias="class")


class SavedBooking(OtfItemBase):
    class_booking_id: int = Field(..., alias="classBookingId")
    class_booking_uuid: str = Field(..., alias="classBookingUUId")
    studio_id: int = Field(..., alias="studioId")
    class_id: int = Field(..., alias="classId")
    is_intro: bool = Field(..., alias="isIntro")
    member_id: int = Field(..., alias="memberId")
    mbo_member_id: str = Field(..., alias="mboMemberId")
    mbo_class_id: int = Field(..., alias="mboClassId")
    mbo_visit_id: None = Field(..., alias="mboVisitId")
    mbo_waitlist_entry_id: None = Field(..., alias="mboWaitlistEntryId")
    mbo_sync_message: None = Field(..., alias="mboSyncMessage")
    status: str
    booked_date: datetime = Field(..., alias="bookedDate")
    checked_in_date: None = Field(..., alias="checkedInDate")
    cancelled_date: None = Field(..., alias="cancelledDate")
    created_by: str | None = Field(None, alias="createdBy")
    created_date: datetime | None = Field(None, alias="createdDate")
    updated_by: str | None = Field(None, alias="updatedBy")
    updated_date: datetime | None = Field(None, alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
    member: Member
    otf_class: Class = Field(..., alias="class")
    custom_data: CustomData = Field(..., alias="customData")
    attributes: dict[str, Any]


class FieldModel(OtfItemBase):
    xsi_nil: str = Field(..., alias="xsiNil")


class FacilitySquareFeet(OtfItemBase):
    field_: FieldModel


class TreatmentRooms(OtfItemBase):
    field_: FieldModel


class Location1(OtfItemBase):
    site_id: str | Any = Field(..., alias="siteId")
    business_description: str | Any = Field(..., alias="businessDescription")
    additional_image_ur_ls: str | Any = Field(..., alias="additionalImageUrLs")
    facility_square_feet: FacilitySquareFeet | Any = Field(..., alias="facilitySquareFeet")
    treatment_rooms: TreatmentRooms | Any = Field(..., alias="treatmentRooms")
    has_classes: str = Field(..., alias="hasClasses")
    id: str
    name: str
    address: str
    address2: str
    tax1: str
    tax2: str
    tax3: str
    tax4: str
    tax5: str
    phone: str
    city: str
    state_prov_code: str = Field(..., alias="stateProvCode")
    postal_code: str = Field(..., alias="postalCode")
    latitude: str
    longitude: str


class MaxCapacity(OtfItemBase):
    field_: FieldModel | Any


class WebCapacity(OtfItemBase):
    field_: FieldModel | Any


class TotalBookedWaitlist(OtfItemBase):
    field_: FieldModel | Any


class WebBooked(OtfItemBase):
    field_: FieldModel | Any


class SemesterId(OtfItemBase):
    field_: FieldModel | Any


class Program(OtfItemBase):
    id: str
    name: str
    schedule_type: str = Field(..., alias="scheduleType")
    cancel_offset: str = Field(..., alias="cancelOffset")


class DefaultTimeLength(OtfItemBase):
    field_: FieldModel


class SessionType(OtfItemBase):
    default_time_length: DefaultTimeLength = Field(..., alias="defaultTimeLength")
    program_id: str = Field(..., alias="programId")
    num_deducted: str = Field(..., alias="numDeducted")
    id: str
    name: str
    site_id: str = Field(..., alias="siteId")
    cross_regional_booking_performed: str = Field(..., alias="crossRegionalBookingPerformed")
    available_for_add_on: str = Field(..., alias="availableForAddOn")


class ClassDescription(OtfItemBase):
    id: str
    name: str
    description: str
    prereq: str
    notes: str
    last_updated: datetime = Field(..., alias="lastUpdated")
    program: Program
    session_type: SessionType = Field(..., alias="sessionType")


class Staff(OtfItemBase):
    email: str
    mobile_phone: str = Field(..., alias="mobilePhone")
    state: str
    country: str
    sort_order: str = Field(..., alias="sortOrder")
    appointment_trn: str = Field(..., alias="appointmentTrn")
    reservation_trn: str = Field(..., alias="reservationTrn")
    independent_contractor: str = Field(..., alias="independentContractor")
    always_allow_double_booking: str = Field(..., alias="alwaysAllowDoubleBooking")
    id: str
    name: str
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    bio: str
    is_male: str = Field(..., alias="isMale")


class AgreementDate(OtfItemBase):
    field_: FieldModel


class ReleasedBy(OtfItemBase):
    field_: FieldModel


class Liability(OtfItemBase):
    is_released: str = Field(..., alias="isReleased")
    agreement_date: AgreementDate = Field(..., alias="agreementDate")
    released_by: ReleasedBy = Field(..., alias="releasedBy")


class FirstAppointmentDate(OtfItemBase):
    field_: FieldModel


class Client(OtfItemBase):
    notes: str
    mobile_provider: str = Field(..., alias="mobileProvider")
    appointment_gender_preference: str = Field(..., alias="appointmentGenderPreference")
    is_company: str = Field(..., alias="isCompany")
    liability_release: str = Field(..., alias="liabilityRelease")
    promotional_email_opt_in: str = Field(..., alias="promotionalEmailOptIn")
    creation_date: datetime = Field(..., alias="creationDate")
    liability: Liability
    unique_id: str = Field(..., alias="uniqueId")
    action: str
    id: str
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str
    email_opt_in: str = Field(..., alias="emailOptIn")
    address_line1: str = Field(..., alias="addressLine1")
    address_line2: str = Field(..., alias="addressLine2")
    city: str
    state: str
    postal_code: str = Field(..., alias="postalCode")
    country: str
    mobile_phone: str = Field(..., alias="mobilePhone")
    home_phone: str = Field(..., alias="homePhone")
    birth_date: datetime = Field(..., alias="birthDate")
    first_appointment_date: FirstAppointmentDate = Field(..., alias="firstAppointmentDate")
    referred_by: str = Field(..., alias="referredBy")
    red_alert: str = Field(..., alias="redAlert")
    is_prospect: str = Field(..., alias="isProspect")
    contact_method: str = Field(..., alias="contactMethod")
    member_uuid: str = Field(..., alias="memberUUId")


class MboClass(OtfItemBase):
    class_schedule_id: str = Field(..., alias="classScheduleId")
    location: Location1
    max_capacity: MaxCapacity = Field(..., alias="maxCapacity")
    web_capacity: WebCapacity = Field(..., alias="webCapacity")
    total_booked: None = Field(..., alias="totalBooked")
    total_booked_waitlist: TotalBookedWaitlist = Field(..., alias="totalBookedWaitlist")
    web_booked: WebBooked = Field(..., alias="webBooked")
    semester_id: SemesterId = Field(..., alias="semesterId")
    is_canceled: str = Field(..., alias="isCanceled")
    substitute: str
    active: str
    is_waitlist_available: str = Field(..., alias="isWaitlistAvailable")
    is_enrolled: str = Field(..., alias="isEnrolled")
    hide_cancel: str = Field(..., alias="hideCancel")
    id: str
    is_available: str = Field(..., alias="isAvailable")
    start_date_time: datetime = Field(..., alias="startDateTime")
    end_date_time: datetime = Field(..., alias="endDateTime")
    class_description: ClassDescription = Field(..., alias="classDescription")
    staff: Staff
    class_uuid: str = Field(..., alias="classUUId")
    client: Client


class MboResponseItem(OtfItemBase):
    class_booking_uuid: str | Any = Field(..., alias="classBookingUUId")
    action: str | Any
    otf_class: MboClass | Any = Field(..., alias="class")


class BookClass(OtfItemBase):
    saved_bookings: list[SavedBooking] = Field(..., alias="savedBookings")
    mbo_response: list[MboResponseItem] = Field(..., alias="mboResponse")
