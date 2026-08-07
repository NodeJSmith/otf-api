from enum import StrEnum


class TrendCategory(StrEnum):
    """Categories that group related workout trend metrics."""

    Effort = "effort"
    Treadmill = "treadmill"
    Rower = "rower"


class TrendType(StrEnum):
    """Available workout stat keys for the trends API."""

    SplatPoints = "splat_points"
    AverageHeartRate = "average_hr"
    PeakHeartRate = "peak_hr"
    TreadmillTopSpeed = "tread_top_speed"
    RowerSplitTime = "rower_500m_split_time"
    RowerTopPower = "rower_top_power"

    @property
    def category(self) -> TrendCategory:
        """Get the category this trend type belongs to."""
        return _TREND_CATEGORY_MAP[self]


_TREND_CATEGORY_MAP: dict[TrendType, TrendCategory] = {
    TrendType.SplatPoints: TrendCategory.Effort,
    TrendType.AverageHeartRate: TrendCategory.Effort,
    TrendType.PeakHeartRate: TrendCategory.Effort,
    TrendType.TreadmillTopSpeed: TrendCategory.Treadmill,
    TrendType.RowerSplitTime: TrendCategory.Rower,
    TrendType.RowerTopPower: TrendCategory.Rower,
}
