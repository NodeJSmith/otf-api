from enum import Enum, StrEnum


class StudioStatus(StrEnum):
    OTHER = "OTHER"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMING_SOON = "Coming Soon"
    TEMP_CLOSED = "Temporarily Closed"
    PERM_CLOSED = "Permanently Closed"


class BookingStatus(StrEnum):
    CheckedIn = "Checked In"
    CancelCheckinPending = "Cancel Checkin Pending"
    CancelCheckinRequested = "Cancel Checkin Requested"
    Cancelled = "Cancelled"
    LateCancelled = "Late Cancelled"
    Booked = "Booked"
    Waitlisted = "Waitlisted"
    CheckinPending = "Checkin Pending"
    CheckinRequested = "Checkin Requested"
    CheckinCancelled = "Checkin Cancelled"


class DoW(StrEnum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class ClassType(StrEnum):
    ORANGE_60_MIN_2G = "Orange 60 Min 2G"
    TREAD_50 = "Tread 50"
    STRENGTH_50 = "Strength 50"
    ORANGE_3G = "Orange 3G"
    ORANGE_60_TORNADO = "Orange 60 - Tornado"
    ORANGE_TORNADO = "Orange Tornado"
    ORANGE_90_MIN_3G = "Orange 90 Min 3G"
    VIP_CLASS = "VIP Class"
    OTHER = "Other"

    @classmethod
    def get_case_insensitive(cls, value: str) -> str:
        lcase_to_actual = {item.value.lower(): item.value for item in cls}
        return lcase_to_actual[value.lower()]

    @staticmethod
    def get_standard_class_types() -> list["ClassType"]:
        """Returns 2G/3G/Tornado - 60/90 minute classes"""
        return [
            ClassType.ORANGE_60_MIN_2G,
            ClassType.ORANGE_3G,
            ClassType.ORANGE_60_TORNADO,
            ClassType.ORANGE_TORNADO,
            ClassType.ORANGE_90_MIN_3G,
        ]

    @staticmethod
    def get_tread_strength_class_types() -> list["ClassType"]:
        """Returns Tread/Strength 50 minute classes"""
        return [ClassType.TREAD_50, ClassType.STRENGTH_50]


class StatsTime(StrEnum):
    LastYear = "lastYear"
    ThisYear = "thisYear"
    LastMonth = "lastMonth"
    ThisMonth = "thisMonth"
    LastWeek = "lastWeek"
    ThisWeek = "thisWeek"
    AllTime = "allTime"


class EquipmentType(int, Enum):
    Treadmill = 2
    Strider = 3
    Rower = 4
    Bike = 5
    WeightFloor = 6
    PowerWalker = 7


class ChallengeType(int, Enum):
    Other = 0
    DriTri = 2
    MarathonMonth = 5
    HellWeek = 52
    Mayhem = 58
    TwelveDaysOfFitness = 63
    Transformation = 64
    RemixInSix = 65
    Push = 66
    BackAtIt = 84
