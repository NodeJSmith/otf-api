from enum import IntEnum, StrEnum


class StatsTime(StrEnum):
    """Enum representing the different time periods for workout statistics."""

    LastYear = "lastYear"
    ThisYear = "thisYear"
    LastMonth = "lastMonth"
    ThisMonth = "thisMonth"
    LastWeek = "lastWeek"
    ThisWeek = "thisWeek"
    AllTime = "allTime"


class EquipmentType(IntEnum):
    """Enum representing the type of equipment used in workouts."""

    Treadmill = 2
    Strider = 3
    Rower = 4
    Bike = 5
    WeightFloor = 6
    PowerWalker = 7


class ChallengeCategory(IntEnum):
    """Enum representing the different challenge categories."""

    Other = 0
    DriTri = 2
    Infinity = 3
    MarathonMonth = 5
    OrangeEverest = 9
    CatchMeIfYouCan = 10
    TwoHundredMeterRow = 15
    FiveHundredMeterRow = 16
    TwoThousandMeterRow = 17
    TwelveMinuteTreadmill = 18
    OneMileTreadmill = 19
    TenMinuteRow = 20
    HellWeek = 52
    Inferno = 55
    Mayhem = 58
    BackAtIt = 60
    FourteenMinuteRow = 61
    TwelveDaysOfFitness = 63
    TransformationChallenge = 64
    RemixInSix = 65
    Push = 66
    QuarterMileTreadmill = 69
    OneThousandMeterRow = 70


class DriTriChallengeSubCategory(IntEnum):
    """Enum representing the subcategories of the DriTri challenge."""

    FullRun = 1
    SprintRun = 3
    Relay = 4
    StrengthRun = 1500


class MarathonMonthChallengeSubCategory(IntEnum):
    """Enum representing the subcategories of the Marathon Month challenge."""

    Original = 1
    Full = 14
    Half = 15
    Ultra = 16
