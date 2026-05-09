from enum import StrEnum
from typing import Self


class BookingStatus(StrEnum):
    """Status of a class booking, from initial request through check-in or cancellation."""

    Pending = "Pending"
    Requested = "Requested"
    Booked = "Booked"
    Cancelled = "Cancelled"
    LateCancelled = "Late Cancelled"
    Waitlisted = "Waitlisted"
    CheckedIn = "Checked In"
    CheckinPending = "Checkin Pending"
    CheckinRequested = "Checkin Requested"
    Confirmed = "Confirmed"
    CheckinCancelled = "Checkin Cancelled"
    CancelCheckinPending = "Cancel Checkin Pending"
    CancelCheckinRequested = "Cancel Checkin Requested"

    def priority(self) -> int:
        """Returns the priority of the booking status for sorting purposes."""
        priorities = {
            BookingStatus.Booked: 0,
            BookingStatus.Confirmed: 1,
            BookingStatus.Waitlisted: 2,
            BookingStatus.Pending: 3,
            BookingStatus.Requested: 4,
            BookingStatus.CheckedIn: 5,
            BookingStatus.CheckinPending: 6,
            BookingStatus.CheckinRequested: 7,
            BookingStatus.CheckinCancelled: 8,
            BookingStatus.Cancelled: 9,
            BookingStatus.LateCancelled: 10,
            BookingStatus.CancelCheckinPending: 11,
            BookingStatus.CancelCheckinRequested: 12,
        }
        return priorities.get(self, 999)


HISTORICAL_BOOKING_STATUSES = [
    BookingStatus.CheckedIn,
    BookingStatus.CancelCheckinPending,
    BookingStatus.CancelCheckinRequested,
    BookingStatus.LateCancelled,
    BookingStatus.CheckinPending,
    BookingStatus.CheckinRequested,
    BookingStatus.CheckinCancelled,
]


class DoW(StrEnum):
    """Day of the week, used for filtering classes by schedule day."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class Orange60ClassType(StrEnum):
    """Subtypes of the standard 60-minute Orange class format."""

    Enterprise60 = "Enterprise 60"
    ExplicitOrange60 = "Explicit Orange 60"
    OpenStudio60_3G = "Open Studio 60 3G"
    Orange3G = "Orange 3G"
    Orange3Group = "Orange 3 Group"
    Orange60 = "Orange 60"
    Orange60Min2G = "Orange 60 Min 2G"
    Orange60Min2GMaskOptional = "Orange 60 Min 2G Mask Optional"
    Orange60Min3G = "Orange 60 Min 3G"
    Orange60Tornado = "Orange 60 - Tornado"
    Tornado60Minute = "Tornado 60 Minute"


class Strength50ClassType(StrEnum):
    """Subtypes of the 50-minute Strength class format."""

    Strength50Lower = "Strength 50 (Lower)"
    Strength50Total = "Strength 50 (Total)"
    Strength50Upper = "Strength 50 (Upper)"


class Tread50ClassType(StrEnum):
    """Subtypes of the 50-minute Tread class format."""

    Tread50 = "Tread 50"


class OtherClassType(StrEnum):
    """Non-standard class types such as workshops, clinics, and special events."""

    InterpretingInbody = "Interpreting Inbody"
    OpenStudio60 = "Open Studio 60"
    Orangetheory101Workshop = "Orangetheory 101 Workshop"
    OrangeTornado = "Orange Tornado"
    OTFPopUp = "OTF Pop-Up"
    PrivateClass = "Private Class"
    RowingClinic = "Rowing Clinic"
    Tornado = "Tornado"
    VIPClass = "VIP Class"


class Orange90ClassType(StrEnum):
    """Subtypes of the 90-minute Orange class format."""

    Orange90Min3G = "Orange 90 Min 3G"
    Orange90Min2G = "Orange 90 Min 2G"
    LifeIsWhyWeGive90 = "Life is Why We Give 90"


class ClassType(StrEnum):
    """High-level classification of OTF class formats."""

    ORANGE_60 = "ORANGE_60"
    ORANGE_90 = "ORANGE_90"
    OTHER = "OTHER"
    STRENGTH_50 = "STRENGTH_50"
    TREAD_50 = "TREAD_50"

    @classmethod
    def get_case_insensitive(cls, value: str) -> "Self":
        """Returns the actual value of the enum, regardless of case."""
        value = (value or "").strip()
        value = value.replace(" ", "_")
        lcase_to_actual = {item.value.lower(): item for item in cls}
        return lcase_to_actual[value.lower()]

    @staticmethod
    def get_standard_class_types() -> list["ClassType"]:
        """Returns 2G/3G/Tornado - 60/90 minute classes."""
        return [ClassType.ORANGE_60, ClassType.ORANGE_90]

    @staticmethod
    def get_tread_strength_class_types() -> list["ClassType"]:
        """Returns Tread/Strength 50 minute classes."""
        return [ClassType.TREAD_50, ClassType.STRENGTH_50]
