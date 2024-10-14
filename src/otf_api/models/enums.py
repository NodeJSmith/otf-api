from enum import Enum


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
