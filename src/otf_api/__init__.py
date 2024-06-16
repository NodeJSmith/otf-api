import os
import sys

from loguru import logger

from . import classes_api, member_api, studios_api, telemetry_api
from .api import Api
from .models.auth import User
from .models.responses import (
    BookingList,
    BookingStatus,
    ChallengeTrackerContent,
    ChallengeTrackerDetailList,
    ChallengeType,
    EquipmentType,
    FavoriteStudioList,
    HistoryClassStatus,
    LatestAgreement,
    MemberDetail,
    MemberMembership,
    MemberPurchaseList,
    OtfClassList,
    OutOfStudioWorkoutHistoryList,
    PerformanceSummaryDetail,
    PerformanceSummaryList,
    StudioDetail,
    StudioDetailList,
    StudioServiceList,
    Telemetry,
    TelemetryHrHistory,
    TelemetryMaxHr,
    TotalClasses,
    WorkoutList,
)

__version__ = "0.2.2"


__all__ = [
    "Api",
    "User",
    "member_api",
    "BookingList",
    "ChallengeTrackerContent",
    "ChallengeTrackerDetailList",
    "ChallengeType",
    "BookingStatus",
    "EquipmentType",
    "HistoryClassStatus",
    "LatestAgreement",
    "MemberDetail",
    "MemberMembership",
    "MemberPurchaseList",
    "OutOfStudioWorkoutHistoryList",
    "StudioServiceList",
    "TotalClasses",
    "WorkoutList",
    "FavoriteStudioList",
    "OtfClassList",
    "classes_api",
    "studios_api",
    "telemetry_api",
    "TelemetryHrHistory",
    "Telemetry",
    "TelemetryMaxHr",
    "StudioDetail",
    "StudioDetailList",
    "PerformanceSummaryDetail",
    "PerformanceSummaryList",
]

logger.remove()
logger.add(sink=sys.stdout, level=os.getenv("OTF_LOG_LEVEL", "INFO"))
