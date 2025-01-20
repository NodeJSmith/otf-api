from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ChallengeCategory, EquipmentType


class MetricEntry(OtfItemBase):
    title: str | None = Field(None, alias="Title")
    equipment_id: EquipmentType | None = Field(None, alias="EquipmentId")
    entry_type: str | None = Field(None, alias="EntryType")
    metric_key: str | None = Field(None, alias="MetricKey")
    min_value: str | None = Field(None, alias="MinValue")
    max_value: str | None = Field(None, alias="MaxValue")


class BenchmarkHistory(OtfItemBase):
    studio_name: str | None = Field(None, alias="StudioName")
    equipment_id: EquipmentType | None = Field(None, alias="EquipmentId")
    class_time: datetime | None = Field(None, alias="ClassTime")
    challenge_sub_category_id: int | None = Field(None, alias="ChallengeSubCategoryId")
    weight_lbs: int | None = Field(None, alias="WeightLBS")
    class_name: str | None = Field(None, alias="ClassName")
    coach_name: str | None = Field(None, alias="CoachName")
    result: float | str | None = Field(None, alias="Result")
    workout_type_id: int | None = Field(None, alias="WorkoutTypeId", exclude=True, repr=False)
    workout_id: int | None = Field(None, alias="WorkoutId", exclude=True, repr=False)
    linked_challenges: list[Any] | None = Field(None, alias="LinkedChallenges", exclude=True, repr=False)

    date_created: datetime | None = Field(
        None,
        alias="DateCreated",
        exclude=True,
        repr=False,
        description="When the entry was created in database, not useful to users",
    )
    date_updated: datetime | None = Field(
        None,
        alias="DateUpdated",
        exclude=True,
        repr=False,
        description="When the entry was updated in database, not useful to users",
    )
    class_id: int | None = Field(None, alias="ClassId", exclude=True, repr=False, description="Not used by API")
    substitute_id: int | None = Field(
        None, alias="SubstituteId", exclude=True, repr=False, description="Not used by API, also always seems to be 0"
    )


class ChallengeHistory(OtfItemBase):
    studio_name: str | None = Field(None, alias="StudioName")
    start_date: datetime | None = Field(None, alias="StartDate")
    end_date: datetime | None = Field(None, alias="EndDate")
    total_result: float | str | None = Field(None, alias="TotalResult")
    is_finished: bool | None = Field(None, alias="IsFinished")
    benchmark_histories: list[BenchmarkHistory] = Field(default_factory=list, alias="BenchmarkHistories")

    challenge_id: int | None = Field(None, alias="ChallengeId", exclude=True, repr=False, description="Not used by API")
    studio_id: int | None = Field(None, alias="StudioId", exclude=True, repr=False, description="Not used by API")
    challenge_objective: str | None = Field(
        None, alias="ChallengeObjective", exclude=True, repr=False, description="Always the string 'None'"
    )


class Goal(OtfItemBase):
    goal: int | None = Field(None, alias="Goal")
    goal_period: str | None = Field(None, alias="GoalPeriod")
    overall_goal: int | None = Field(None, alias="OverallGoal")
    overall_goal_period: str | None = Field(None, alias="OverallGoalPeriod")
    min_overall: int | None = Field(None, alias="MinOverall")
    min_overall_period: str | None = Field(None, alias="MinOverallPeriod")


class FitnessBenchmark(OtfItemBase):
    challenge_category_id: ChallengeCategory | None = Field(None, alias="ChallengeCategoryId")
    challenge_sub_category_id: int | None = Field(None, alias="ChallengeSubCategoryId")
    equipment_id: EquipmentType = Field(None, alias="EquipmentId")
    equipment_name: str | None = Field(None, alias="EquipmentName")
    metric_entry: MetricEntry | None = Field(None, alias="MetricEntry")
    challenge_name: str | None = Field(None, alias="ChallengeName")
    best_record: float | str | None = Field(None, alias="BestRecord")
    last_record: float | str | None = Field(None, alias="LastRecord")
    previous_record: float | str | None = Field(None, alias="PreviousRecord")
    unit: str | None = Field(None, alias="Unit")
    goals: Goal | None = Field(None, alias="Goals")
    challenge_histories: list[ChallengeHistory] = Field(default_factory=list, alias="ChallengeHistories")
