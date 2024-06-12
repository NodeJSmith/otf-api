from enum import Enum


class StudioStatus(str, Enum):
    OTHER = "OTHER"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMING_SOON = "Coming Soon"
    TEMP_CLOSED = "Temporarily Closed"
    PERM_CLOSED = "Permanently Closed"

    @classmethod
    def all_statuses(cls) -> list[str]:
        return list(cls.__members__.values())


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

    @classmethod
    def map_to_time(cls, challenge_type: "ChallengeType") -> int:
        mapping = {
            "MultiWeek": [cls.Transformation, cls.BackAtIt],
            "MultiDay": [cls.Mayhem, cls.RemixInSix, cls.HellWeek, cls.Push, cls.TwelveDaysOfFitness],
            "Other": [cls.Other, cls.MarathonMonth, cls.DriTri],
        }
        for key, value in mapping.items():
            if challenge_type in value:
                return key

        raise ValueError(f"Could not map {challenge_type} to a time type")

    @classmethod
    def from_api_name(cls, name: str) -> "ChallengeType":
        match name:
            case "12 DAYS OF FITNESS":
                return cls.TwelveDaysOfFitness
            case "ALL OUT MAYHEM":
                return cls.Mayhem
            case "HELL WEEK":
                return cls.HellWeek
            case "MARATHON MONTH":
                return cls.MarathonMonth
            case "PUSH 30":
                return cls.Push
            case "TRANSFORMATION CHALLENGE":
                return cls.Transformation
            case "DRITRI":
                return cls.DriTri
            case _:
                return cls.Other


class BookingStatus(str, Enum):
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

    @classmethod
    def all_statuses(cls) -> list[str]:
        return list(cls.__members__.values())


class HistoryBookingStatus(str, Enum):
    Attended = "Attended"
    Cancelled = "Cancelled"
    LateCancelled = "Late Cancelled"

    @classmethod
    def all_statuses(cls) -> list[str]:
        return list(cls.__members__.values())


class HistoryClassStatus(str, Enum):
    CheckedIn = "Checked In"
    CancelCheckinPending = "Cancel Checkin Pending"
    CancelCheckinRequested = "Cancel Checkin Requested"
    LateCancelled = "Late Cancelled"
    Booked = "Booked"
    Waitlisted = "Waitlisted"
    CheckinPending = "Checkin Pending"
    CheckinRequested = "Checkin Requested"
    CheckinCancelled = "Checkin Cancelled"
    Pending = "Pending"
    Confirmed = "Confirmed"
    Requested = "Requested"

    @classmethod
    def all_statuses(cls) -> list[str]:
        return list(cls.__members__.values())


ALL_CLASS_STATUS = BookingStatus.all_statuses()
ALL_HISTORY_CLASS_STATUS = HistoryClassStatus.all_statuses()
ALL_STUDIO_STATUS = StudioStatus.all_statuses()
