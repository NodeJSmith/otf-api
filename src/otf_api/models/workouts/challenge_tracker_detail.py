from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase

from .enums import EquipmentType


class MetricEntry(OtfItemBase):
    title: str | None = Field(None, validation_alias="Title")
    equipment_id: EquipmentType | None = Field(None, validation_alias="EquipmentId")
    entry_type: str | None = Field(None, validation_alias="EntryType")
    metric_key: str | None = Field(None, validation_alias="MetricKey")
    min_value: str | None = Field(None, validation_alias="MinValue")
    max_value: str | None = Field(None, validation_alias="MaxValue")


class BenchmarkHistory(OtfItemBase):
    studio_name: str | None = Field(None, validation_alias="StudioName")
    equipment_id: EquipmentType | None = Field(None, validation_alias="EquipmentId")
    class_time: datetime | None = Field(None, validation_alias="ClassTime")
    challenge_sub_category_id: int | None = Field(None, validation_alias="ChallengeSubCategoryId")
    weight_lbs: int | None = Field(None, validation_alias="WeightLBS")
    class_name: str | None = Field(None, validation_alias="ClassName")
    coach_name: str | None = Field(None, validation_alias="CoachName")
    result: float | str | None = Field(None, validation_alias="Result")
    workout_type_id: int | None = Field(None, validation_alias="WorkoutTypeId", exclude=True, repr=False)
    workout_id: int | None = Field(None, validation_alias="WorkoutId", exclude=True, repr=False)
    linked_challenges: list[Any] | None = Field(None, validation_alias="LinkedChallenges", exclude=True, repr=False)

    date_created: datetime | None = Field(
        None,
        validation_alias="DateCreated",
        exclude=True,
        repr=False,
        description="When the entry was created in database, not useful to users",
    )
    date_updated: datetime | None = Field(
        None,
        validation_alias="DateUpdated",
        exclude=True,
        repr=False,
        description="When the entry was updated in database, not useful to users",
    )
    class_id: int | None = Field(
        None, validation_alias="ClassId", exclude=True, repr=False, description="Not used by API"
    )
    substitute_id: int | None = Field(
        None,
        validation_alias="SubstituteId",
        exclude=True,
        repr=False,
        description="Not used by API, also always seems to be 0",
    )


class ChallengeHistory(OtfItemBase):
    studio_name: str | None = Field(None, validation_alias="StudioName")
    start_date: datetime | None = Field(None, validation_alias="StartDate")
    end_date: datetime | None = Field(None, validation_alias="EndDate")
    total_result: float | str | None = Field(None, validation_alias="TotalResult")
    is_finished: bool | None = Field(None, validation_alias="IsFinished")
    benchmark_histories: list[BenchmarkHistory] = Field(default_factory=list, validation_alias="BenchmarkHistories")

    challenge_id: int | None = Field(
        None, validation_alias="ChallengeId", exclude=True, repr=False, description="Not used by API"
    )
    studio_id: int | None = Field(
        None, validation_alias="StudioId", exclude=True, repr=False, description="Not used by API"
    )
    challenge_objective: str | None = Field(
        None, validation_alias="ChallengeObjective", exclude=True, repr=False, description="Always the string 'None'"
    )


class Goal(OtfItemBase):
    goal: int | None = Field(None, validation_alias="Goal")
    goal_period: str | None = Field(None, validation_alias="GoalPeriod")
    overall_goal: int | None = Field(None, validation_alias="OverallGoal")
    overall_goal_period: str | None = Field(None, validation_alias="OverallGoalPeriod")
    min_overall: int | None = Field(None, validation_alias="MinOverall")
    min_overall_period: str | None = Field(None, validation_alias="MinOverallPeriod")


class FitnessBenchmark(OtfItemBase):
    challenge_category_id: int | None = Field(None, validation_alias="ChallengeCategoryId")
    challenge_sub_category_id: int | None = Field(None, validation_alias="ChallengeSubCategoryId")
    equipment_id: EquipmentType | None = Field(None, validation_alias="EquipmentId")
    equipment_name: str | None = Field(None, validation_alias="EquipmentName")
    metric_entry: MetricEntry | None = Field(None, validation_alias="MetricEntry")
    challenge_name: str | None = Field(None, validation_alias="ChallengeName")
    best_record: float | str | None = Field(None, validation_alias="BestRecord")
    last_record: float | str | None = Field(None, validation_alias="LastRecord")
    previous_record: float | str | None = Field(None, validation_alias="PreviousRecord")
    unit: str | None = Field(None, validation_alias="Unit")
    goals: Goal | None = Field(None, validation_alias="Goals")
    challenge_histories: list[ChallengeHistory] = Field(default_factory=list, validation_alias="ChallengeHistories")
