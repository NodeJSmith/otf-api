from .book_class import BookClass
from .bookings import BookingList, BookingStatus
from .cancel_booking import CancelBooking
from .challenge_tracker_content import ChallengeTrackerContent
from .challenge_tracker_detail import ChallengeTrackerDetailList
from .classes import OtfClassList
from .enums import ChallengeType, EquipmentType, HistoryClassStatus
from .favorite_studios import FavoriteStudioList
from .latest_agreement import LatestAgreement
from .member_detail import MemberDetail
from .member_membership import MemberMembership
from .member_purchases import MemberPurchaseList
from .out_of_studio_workout_history import OutOfStudioWorkoutHistoryList
from .performance_summary_detail import PerformanceSummaryDetail
from .performance_summary_list import PerformanceSummaryList
from .studio_detail import StudioDetail, StudioDetailList
from .studio_services import StudioServiceList
from .telemetry import Telemetry
from .telemetry_hr_history import TelemetryHrHistory
from .telemetry_max_hr import TelemetryMaxHr
from .total_classes import TotalClasses
from .workouts import WorkoutList

__all__ = [
    "BookingList",
    "ChallengeTrackerContent",
    "ChallengeTrackerDetailList",
    "LatestAgreement",
    "MemberDetail",
    "MemberMembership",
    "MemberPurchaseList",
    "OutOfStudioWorkoutHistoryList",
    "StudioServiceList",
    "TotalClasses",
    "WorkoutList",
    "ChallengeType",
    "BookingStatus",
    "EquipmentType",
    "HistoryClassStatus",
    "StudioStatus",
    "FavoriteStudioList",
    "OtfClassList",
    "TelemetryHrHistory",
    "Telemetry",
    "TelemetryMaxHr",
    "StudioDetail",
    "StudioDetailList",
    "PerformanceSummaryDetail",
    "PerformanceSummaryList",
    "BookClass",
    "CancelBooking",
]
