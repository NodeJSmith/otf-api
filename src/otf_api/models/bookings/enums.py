from enum import StrEnum
from typing import Self


class BookingStatus(StrEnum):
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
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class Orange60ClassType(StrEnum):
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
    Strength50Lower = "Strength 50 (Lower)"
    Strength50Total = "Strength 50 (Total)"
    Strength50Upper = "Strength 50 (Upper)"


class Tread50ClassType(StrEnum):
    Tread50 = "Tread 50"


class OtherClassType(StrEnum):
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
    Orange90Min3G = "Orange 90 Min 3G"
    Orange90Min2G = "Orange 90 Min 2G"
    LifeIsWhyWeGive90 = "Life is Why We Give 90"


class ClassType(StrEnum):
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
