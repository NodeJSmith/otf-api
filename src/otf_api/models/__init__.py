from .body_composition_list import BodyCompositionList
from .book_class import BookClass
from .bookings import Booking, BookingList
from .cancel_booking import CancelBooking
from .challenge_tracker_content import ChallengeTrackerContent
from .challenge_tracker_detail import ChallengeTrackerDetailList
from .classes import OtfClass, OtfClassList
from .enums import BookingStatus, ChallengeType, ClassType, DoW, EquipmentType, StatsTime, StudioStatus
from .favorite_studios import FavoriteStudioList
from .latest_agreement import LatestAgreement
from .lifetime_stats import StatsResponse
from .member_detail import MemberDetail
from .member_membership import MemberMembership
from .member_purchases import MemberPurchaseList
from .out_of_studio_workout_history import OutOfStudioWorkoutHistoryList
from .performance_summary_detail import PerformanceSummaryDetail
from .performance_summary_list import PerformanceSummaryList
from .studio_detail import Pagination, StudioDetail, StudioDetailList
from .studio_services import StudioServiceList
from .telemetry import Telemetry
from .telemetry_hr_history import TelemetryHrHistory
from .telemetry_max_hr import TelemetryMaxHr
from .total_classes import TotalClasses

__all__ = [
    "BodyCompositionList",
    "BookClass",
    "Booking",
    "BookingList",
    "BookingStatus",
    "CancelBooking",
    "ChallengeTrackerContent",
    "ChallengeTrackerDetailList",
    "ChallengeType",
    "ClassType",
    "DoW",
    "EquipmentType",
    "FavoriteStudioList",
    "LatestAgreement",
    "MemberDetail",
    "MemberMembership",
    "MemberPurchaseList",
    "OtfClassList",
    "OtfClass",
    "OutOfStudioWorkoutHistoryList",
    "Pagination",
    "PerformanceSummaryDetail",
    "PerformanceSummaryList",
    "StatsResponse",
    "StatsTime",
    "StudioDetail",
    "StudioDetailList",
    "StudioServiceList",
    "StudioStatus",
    "Telemetry",
    "TelemetryHrHistory",
    "TelemetryMaxHr",
    "TotalClasses",
]
