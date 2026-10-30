"""Tests for WorkoutApi read-only methods."""

from datetime import date
from unittest.mock import patch

import pytest
from conftest import load_fixture

from otf_api.models.workouts import (
    BodyCompositionData,
    ChallengeCategory,
    ChallengeTracker,
    EquipmentType,
    FitnessBenchmark,
    InStudioStatsData,
    OutOfStudioWorkoutHistory,
    OutStudioStatsData,
    StatsTime,
    Telemetry,
    TelemetryHistoryItem,
    Workout,
)
from otf_api.models.workouts.challenge_tracker_content import Benchmark
from otf_api.models.workouts.challenge_tracker_detail import BenchmarkHistory, MetricEntry


def test_get_body_composition_list(mock_otf) -> None:
    result = mock_otf.workouts.get_body_composition_list()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, BodyCompositionData) for item in result)

    first = result[0]
    assert isinstance(first.body_mass_index, float)


def test_get_challenge_tracker(mock_otf) -> None:
    result = mock_otf.workouts.get_challenge_tracker()

    assert isinstance(result, ChallengeTracker)
    assert isinstance(result.benchmarks, list)


def test_get_benchmarks_by_equipment(mock_otf) -> None:
    result = mock_otf.workouts.get_benchmarks_by_equipment(EquipmentType.Treadmill)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(b, FitnessBenchmark) for b in result)

    first = result[0]
    assert first.equipment_id == EquipmentType.Treadmill


@pytest.mark.parametrize(
    ["model", "raw"],
    [
        (Benchmark, {"EquipmentId": 99}),
        (FitnessBenchmark, {"EquipmentId": 99}),
        (MetricEntry, {"EquipmentId": 99}),
        (BenchmarkHistory, {"EquipmentId": 99}),
    ],
)
def test_unrecognized_equipment_id_is_kept_raw(model, raw) -> None:
    result = model.model_validate(raw)

    assert result.equipment_id == 99
    assert not isinstance(result.equipment_id, EquipmentType)


def test_known_and_null_equipment_id_pass_through() -> None:
    assert FitnessBenchmark.model_validate({"EquipmentId": 2}).equipment_id is EquipmentType.Treadmill
    assert FitnessBenchmark.model_validate({"EquipmentId": None}).equipment_id is None


def test_get_benchmarks_by_equipment_accepts_a_value_read_from_a_response(mock_otf) -> None:
    benchmarks = load_fixture("workouts/get_benchmarks")["Dto"][:1]
    benchmarks[0]["EquipmentId"] = 99

    with patch.object(mock_otf.workouts.client, "get_benchmarks", return_value=benchmarks):
        result = mock_otf.workouts.get_benchmarks_by_equipment(99)

    assert len(result) == 1
    assert result[0].equipment_id == 99


def test_get_benchmarks_by_challenge_category(mock_otf) -> None:
    result = mock_otf.workouts.get_benchmarks_by_challenge_category(ChallengeCategory.DriTri)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(b, FitnessBenchmark) for b in result)

    first = result[0]
    assert first.challenge_category_id == ChallengeCategory.DriTri


def test_get_challenge_tracker_detail(mock_otf) -> None:
    result = mock_otf.workouts.get_challenge_tracker_detail(ChallengeCategory.DriTri)

    assert isinstance(result, FitnessBenchmark)
    assert result.challenge_name is not None


def test_get_hr_history(mock_otf) -> None:
    result = mock_otf.workouts.get_hr_history()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, TelemetryHistoryItem) for item in result)

    first = result[0]
    assert first.max_hr_value is not None
    assert isinstance(first.max_hr_value, int)


def test_get_telemetry(mock_otf) -> None:
    # use a performance_summary_id that has a telemetry fixture
    perf_id = "42d6cb5c-6ed4-494b-9fc9-e3b11fcff454"
    result = mock_otf.workouts.get_telemetry(perf_id)

    assert isinstance(result, Telemetry)
    assert result.member_uuid != ""
    assert result.zones is not None
    assert len(result.telemetry) > 0


def test_get_member_lifetime_stats_in_studio(mock_otf) -> None:
    result = mock_otf.workouts.get_member_lifetime_stats_in_studio()

    assert isinstance(result, InStudioStatsData)


def test_get_member_lifetime_stats_in_studio_this_month(mock_otf) -> None:
    result = mock_otf.workouts.get_member_lifetime_stats_in_studio(StatsTime.ThisMonth)

    assert isinstance(result, InStudioStatsData)


def test_get_member_lifetime_stats_out_of_studio(mock_otf) -> None:
    result = mock_otf.workouts.get_member_lifetime_stats_out_of_studio()

    assert isinstance(result, OutStudioStatsData)


def test_get_out_of_studio_workout_history(mock_otf) -> None:
    result = mock_otf.workouts.get_out_of_studio_workout_history()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(w, OutOfStudioWorkoutHistory) for w in result)

    first = result[0]
    assert isinstance(first.member_uuid, str)
    assert first.member_uuid != ""


def test_get_workouts(mock_otf) -> None:
    # dates flow through to get_bookings_new, which must match fixture URL params
    result = mock_otf.workouts.get_workouts(
        start_date=date(2026, 3, 27),
        end_date=date(2026, 4, 26),
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(w, Workout) for w in result)

    first = result[0]
    assert isinstance(first.performance_summary_id, str)
    assert first.performance_summary_id != ""
