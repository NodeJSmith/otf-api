from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import BookingStatus, StudioStatus
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin


class CountryCurrency(OtfItemBase):
    country_currency_code: str = Field(..., alias="countryCurrencyCode")
    currency_id: int | None = Field(None, alias=AliasPath("defaultCurrency", "currencyId"))
    currency_alphabetic_code: str | None = Field(None, alias=AliasPath("defaultCurrency", "currencyAlphabeticCode"))


class Location(PhoneLongitudeLatitudeMixin, AddressMixin):
    distance: float | None = Field(None, alias="distance", exclude=True, repr=False)
    location_name: str | None = Field(None, alias="locationName", exclude=True, repr=False)


class StudioLocation(PhoneLongitudeLatitudeMixin, AddressMixin):
    physical_region: str | None = Field(None, alias="physicalRegion", exclude=True, repr=False)
    physical_country_id: int | None = Field(None, alias="physicalCountryId", exclude=True, repr=False)
    country_currency: CountryCurrency | None = Field(None, alias="country_currency", exclude=True, repr=False)


class Studio(OtfItemBase):
    studio_uuid: str = Field(alias="studioUUId")
    studio_name: str = Field(alias="studioName")
    description: str | None = None
    status: StudioStatus | None = None
    time_zone: str = Field(alias="timeZone")

    # unused fields
    allows_cr_waitlist: bool | None = Field(None, alias="allowsCRWaitlist")
    contact_email: str | None = Field(None, alias="contactEmail", exclude=True)
    cr_waitlist_flag_last_updated: datetime | None = Field(None, alias="crWaitlistFlagLastUpdated", exclude=True)
    logo_url: str | None = Field(None, alias="logoUrl", exclude=True)
    mbo_studio_id: int | None = Field(None, alias="mboStudioId", exclude=True, description="MindBody attr")
    studio_id: int = Field(alias="studioId", exclude=True, description="Not used by API")
    studio_location: StudioLocation | None = Field(None, alias="studioLocation", exclude=True)


class Coach(OtfItemBase):
    coach_uuid: str = Field(alias="coachUUId")
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")

    # unused fields
    image_url: str | None = Field(None, alias="imageUrl", exclude=True)
    name: str = Field(exclude=True)
    profile_picture_url: str | None = Field(None, alias="profilePictureUrl", exclude=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class OtfClass(OtfItemBase):
    class_uuid: str = Field(alias="classUUId")
    name: str
    starts_at: datetime = Field(alias="startDateTime", description="Start time in local timezone")
    ends_at: datetime = Field(alias="endDateTime", description="End time in local timezone")
    is_available: bool = Field(alias="isAvailable")
    is_cancelled: bool = Field(alias="isCancelled")
    studio: Studio
    coach: Coach

    # unused fields
    coach_id: int | None = Field(None, alias="coachId", exclude=True, description="Not used by API")
    description: str | None = Field(None, exclude=True)
    location: Location | None = Field(None, exclude=True)
    program_name: str | None = Field(None, alias="programName", exclude=True)
    virtual_class: bool | None = Field(None, alias="virtualClass", exclude=True)

    @property
    def starts_at_local(self) -> datetime:
        """Alias for starts_at, kept to avoid breaking changes"""
        return self.starts_at

    @property
    def ends_at_local(self) -> datetime:
        """Alias for ends_at, kept to avoid breaking changes"""
        return self.ends_at


class Member(OtfItemBase):
    member_uuid: str = Field(alias="memberUUId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    gender: str | None = None
    cc_last_4: str | None = Field(None, alias="ccLast4", exclude=True)


class Booking(OtfItemBase):
    booking_uuid: str = Field(alias="classBookingUUId", description="ID used to cancel the booking")
    is_intro: bool = Field(alias="isIntro")
    status: BookingStatus
    booked_date: datetime | None = Field(None, alias="bookedDate")
    checked_in_date: datetime | None = Field(None, alias="checkedInDate")
    cancelled_date: datetime | None = Field(None, alias="cancelledDate")
    created_date: datetime = Field(alias="createdDate")
    updated_date: datetime = Field(alias="updatedDate")
    is_deleted: bool = Field(alias="isDeleted")
    waitlist_position: int | None = Field(None, alias="waitlistPosition")
    otf_class: OtfClass = Field(alias="class")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")

    # unused fields
    class_booking_id: int = Field(alias="classBookingId", exclude=True, description="Not used by API")
    class_id: int = Field(alias="classId", exclude=True, description="Not used by API")
    created_by: str = Field(alias="createdBy", exclude=True)
    mbo_class_id: int | None = Field(None, alias="mboClassId", exclude=True, description="MindBody attr")
    mbo_member_id: str | None = Field(None, alias="mboMemberId", exclude=True, description="MindBody attr")
    mbo_sync_message: str | None = Field(None, alias="mboSyncMessage", exclude=True, description="MindBody attr")
    mbo_visit_id: int | None = Field(None, alias="mboVisitId", exclude=True, description="MindBody attr")
    mbo_waitlist_entry_id: int | None = Field(None, alias="mboWaitlistEntryId", exclude=True)
    member_id: int = Field(alias="memberId", exclude=True, description="Not used by API")
    member: Member | None = Field(None, exclude=True, description="Slimmed down member object")
    studio_id: int = Field(alias="studioId", exclude=True, description="Not used by API")
    updated_by: str = Field(alias="updatedBy", exclude=True)

    @property
    def class_uuid(self) -> str:
        """Shortcut to get the class UUID"""
        return self.otf_class.class_uuid

    @property
    def starts_at(self) -> datetime:
        """Shortcut to get the class start time"""
        return self.otf_class.starts_at

    @property
    def ends_at(self) -> datetime:
        """Shortcut to get the class end time"""
        return self.otf_class.ends_at

    def __str__(self) -> str:
        starts_at_str = self.otf_class.starts_at.strftime("%a %b %d, %I:%M %p")
        class_name = self.otf_class.name
        coach_name = self.otf_class.coach.name
        booked_str = self.status.value

        return f"Booking: {starts_at_str} {class_name} - {coach_name} ({booked_str})"


class BookingList(OtfItemBase):
    bookings: list[Booking]

    def __len__(self) -> int:
        return len(self.bookings)

    def __iter__(self):
        return iter(self.bookings)

    def get_booking_from_class_uuid(self, class_uuid: str) -> Booking | None:
        for booking in self.bookings:
            if booking.otf_class.class_uuid == class_uuid:
                return booking
        return None

    def __getitem__(self, item) -> Booking:
        return self.bookings[item]
