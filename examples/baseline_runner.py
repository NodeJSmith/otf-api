"""Run read-only examples and capture structured output for regression comparison.

Usage: uv run python examples/baseline_runner.py > /tmp/otf-baseline.json
"""

import json
import sys
import traceback
from contextlib import suppress

from otf_api import Otf
from otf_api.models.workouts import ChallengeCategory, EquipmentType, StatsTime


def capture(label: str, func: callable, results: dict) -> None:  # noqa: D103
    try:
        val = func()
        if hasattr(val, "model_dump"):
            results[label] = val.model_dump(mode="json")
        elif isinstance(val, list) and val and hasattr(val[0], "model_dump"):
            results[label] = [v.model_dump(mode="json") for v in val]
        else:
            results[label] = val
        print(f"  OK: {label} ({type(val).__name__})", file=sys.stderr)
    except Exception as e:
        results[label] = {"__error__": str(e), "__traceback__": traceback.format_exc()}
        print(f"  FAIL: {label} — {e}", file=sys.stderr)


def main() -> None:  # noqa: D103
    results: dict = {}

    print("Initializing Otf client...", file=sys.stderr)
    otf = Otf()
    results["home_studio_uuid"] = otf.home_studio_uuid

    # --- Studios ---
    print("Studios...", file=sys.stderr)
    capture("studios.search_by_geo", lambda: otf.studios.search_studios_by_geo(), results)
    capture("studios.get_detail_home", lambda: otf.studios.get_studio_detail(), results)
    capture("studios.get_favorites", lambda: otf.studios.get_favorite_studios(), results)

    home = results.get("studios.get_detail_home", {})
    if isinstance(home, dict) and "studio_uuid" in home:
        capture(
            "studios.get_services",
            lambda: otf.studios.get_studio_services(home["studio_uuid"]),
            results,
        )

    # --- Bookings ---
    print("Bookings...", file=sys.stderr)
    capture("bookings.get_bookings", lambda: otf.bookings.get_bookings(), results)
    capture("bookings.get_bookings_new", lambda: otf.bookings.get_bookings_new(), results)
    capture("bookings.get_classes", lambda: otf.bookings.get_classes(), results)

    # --- Workouts ---
    print("Workouts...", file=sys.stderr)
    capture(
        "workouts.lifetime_stats_in_studio",
        lambda: otf.workouts.get_member_lifetime_stats_in_studio(),
        results,
    )
    capture(
        "workouts.lifetime_stats_in_studio_this_month",
        lambda: otf.workouts.get_member_lifetime_stats_in_studio(StatsTime.ThisMonth),
        results,
    )
    capture(
        "workouts.lifetime_stats_out_of_studio",
        lambda: otf.workouts.get_member_lifetime_stats_out_of_studio(),
        results,
    )
    capture("workouts.get_workouts", lambda: otf.workouts.get_workouts(), results)
    capture("workouts.get_hr_history", lambda: otf.workouts.get_hr_history(), results)

    # Get a workout from a booking (if any have workout data)
    bookings_new = results.get("bookings.get_bookings_new")
    if isinstance(bookings_new, list):
        for b_data in bookings_new:
            if isinstance(b_data, dict) and b_data.get("workout"):
                booking_id = b_data["booking_id"]
                capture(
                    "workouts.get_workout_from_booking",
                    lambda: otf.workouts.get_workout_from_booking(booking_id),
                    results,
                )
                break

    # --- Challenges ---
    print("Challenges...", file=sys.stderr)
    for et in EquipmentType:
        with suppress(Exception):
            benchmarks = otf.workouts.get_benchmarks_by_equipment(et)
            if benchmarks:
                results[f"challenges.equipment.{et.name}"] = [b.model_dump(mode="json") for b in benchmarks]
                print(f"  OK: challenges.equipment.{et.name} ({len(benchmarks)} entries)", file=sys.stderr)

    for ct in ChallengeCategory:
        with suppress(Exception):
            benchmarks = otf.workouts.get_benchmarks_by_challenge_category(ct)
            if benchmarks:
                results[f"challenges.category.{ct.name}"] = [b.model_dump(mode="json") for b in benchmarks]
                print(f"  OK: challenges.category.{ct.name} ({len(benchmarks)} entries)", file=sys.stderr)

    # --- Summary ---
    errors = {k: v for k, v in results.items() if isinstance(v, dict) and "__error__" in v}
    print(f"\nDone: {len(results)} captures, {len(errors)} errors", file=sys.stderr)
    if errors:
        for k, v in errors.items():
            print(f"  ERROR {k}: {v['__error__']}", file=sys.stderr)

    json.dump(results, sys.stdout, indent=2, default=str)
    print(file=sys.stdout)


if __name__ == "__main__":
    main()
