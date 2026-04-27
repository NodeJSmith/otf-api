"""Rename anonymized fixture files from URL-slugs to semantic names.

Reads _meta.json for URL-to-file mappings, renames into namespace subdirectories
with human-readable names, and writes an updated index.json for the mock transport.

Usage:
    uv run python scripts/rename_fixtures.py [fixture_dir]
"""

import json
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote

FIXTURE_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fixtures/anonymized")

EQUIPMENT_IDS = {
    "2": "treadmill",
    "3": "strider",
    "4": "rower",
    "5": "bike",
    "6": "weight_floor",
    "7": "power_walker",
}

CHALLENGE_TYPE_IDS = {
    "0": "other",
    "2": "dri_tri",
    "3": "infinity",
    "5": "marathon_month",
    "9": "orange_everest",
    "10": "catch_me_if_you_can",
    "15": "two_hundred_meter_row",
    "16": "five_hundred_meter_row",
    "17": "two_thousand_meter_row",
    "18": "twelve_minute_treadmill",
    "19": "one_mile_treadmill",
    "20": "ten_minute_row",
    "52": "hell_week",
    "55": "inferno",
    "58": "mayhem",
    "60": "back_at_it",
    "61": "fourteen_minute_row",
    "63": "twelve_days_of_fitness",
    "64": "transformation_challenge",
    "65": "remix_in_six",
    "66": "push",
    "69": "quarter_mile_treadmill",
    "70": "one_thousand_meter_row",
}


def classify_file(file_entry: dict) -> tuple[str, str]:
    """Return (namespace/filename, description) for a file entry from _meta.json."""
    path = file_entry["path"]
    params_str = file_entry.get("params", "")
    params = parse_qs(unquote(params_str))
    host = file_entry["file"].split("/")[0]

    # --- Members ---
    if "/member/members/" in path and path.endswith(("/memberships",)):
        return "members/get_member_membership.json", "Member membership details"

    if "/member/members/" in path and path.endswith("/purchases"):
        return "members/get_member_purchases.json", "Member purchases"

    if "/member/members/" in path and "include" in params:
        return "members/get_member_detail.json", "Member detail with addresses and class summary"

    if "/sms/v1/preferences" in path:
        return "members/get_sms_notification_settings.json", "SMS notification preferences"

    if "/otfmailing/v2/preferences" in path:
        return "members/get_email_notification_settings.json", "Email notification preferences"

    # --- Studios ---
    if path.startswith("/mobile/v1/studios/"):
        studio_uuid = path.split("/")[-1]
        return f"studios/get_studio_detail__{studio_uuid[:8]}.json", f"Studio detail for {studio_uuid[:8]}"

    if path == "/mobile/v1/studios" and "latitude" in params:
        return "studios/search_studios_by_geo.json", "Studios by geographic search"

    if "/favorite-studios" in path:
        return "studios/get_favorite_studios.json", "Favorite studios"

    if "/member/studios/" in path and "/services" in path:
        return "studios/get_studio_services.json", "Studio services"

    # --- Bookings ---
    if path == "/v1/classes":
        return "bookings/get_classes.json", "Available classes"

    if "/member/members/" in path and "/bookings" in path and "statuses" in params:
        return "bookings/get_bookings.json", "Member bookings (filtered by status)"

    if "/member/members/" in path and "/bookings" in path and "statuses" not in params:
        return "bookings/get_bookings_all.json", "Member bookings (all statuses)"

    if path == "/v1/bookings/me":
        starts = params.get("starts_after", [""])[0][:10]
        return f"bookings/get_bookings_new__{starts}.json", f"New bookings endpoint (from {starts})"

    # --- Workouts ---
    if "/body-composition" in path:
        return "workouts/get_body_composition_list.json", "Body composition history"

    if "/challenges/v3.1/member/" in path:
        return "workouts/get_challenge_tracker.json", "Challenge tracker overview"

    if "/challenges/v1/member/" in path and "/participation" in path:
        ct = params.get("challengeTypeId", [""])[0]
        name = CHALLENGE_TYPE_IDS.get(ct, ct)
        return f"workouts/get_challenge_tracker_detail__{name}.json", f"Challenge detail: {name}"

    if "/challenges/v3/member/" in path and "/benchmarks" in path:
        eq_id = params.get("equipmentId", ["0"])[0]
        ct_id = params.get("challengeTypeId", ["0"])[0]

        if eq_id != "0" and ct_id == "0":
            name = EQUIPMENT_IDS.get(eq_id, eq_id)
            return f"workouts/get_benchmarks_by_equipment__{name}.json", f"Benchmarks: equipment {name}"
        elif ct_id != "0" and eq_id == "0":
            name = CHALLENGE_TYPE_IDS.get(ct_id, ct_id)
            return f"workouts/get_benchmarks_by_challenge__{name}.json", f"Benchmarks: challenge {name}"
        else:
            return "workouts/get_benchmarks.json", "Benchmarks (all)"

    if "/performance/v2/" in path and "/over-time/" in path:
        time_period = path.split("/")[-1]
        return f"workouts/get_lifetime_stats__{time_period}.json", f"Lifetime stats: {time_period}"

    if "/out-of-studio-workout" in path:
        return "workouts/get_out_of_studio_workout_history.json", "Out-of-studio workout history"

    if "/v1/physVars/maxHr/history" in path:
        return "workouts/get_hr_history.json", "Heart rate history"

    if path == "/v1/performance/summary" and "classHistoryUuid" in params:
        uuid = params["classHistoryUuid"][0]
        return f"workouts/get_telemetry__{uuid[:8]}.json", f"Telemetry for class {uuid[:8]}"

    if path.startswith("/v1/performance-summaries/"):
        uuid = path.split("/")[-1]
        return f"workouts/get_workout__{uuid[:8]}.json", f"Workout performance summary {uuid[:8]}"

    if path == "/v1/performance-summaries":
        return "workouts/get_workouts.json", "Workout list (performance summaries)"

    return f"unknown/{file_entry['file'].replace('/', '__')}", "Unclassified"


def main() -> None:
    meta_path = FIXTURE_DIR / "_meta.json"
    if not meta_path.exists():
        print(f"Error: {meta_path} not found")
        sys.exit(1)

    meta = json.loads(meta_path.read_text())

    # Track renames and handle collisions
    renames: list[tuple[Path, Path, dict]] = []
    seen_targets: dict[str, int] = {}

    for file_entry in meta["files"]:
        old_rel = file_entry["file"]
        old_path = FIXTURE_DIR / old_rel

        if not old_path.exists():
            print(f"  SKIP (missing): {old_rel}")
            continue

        new_rel, description = classify_file(file_entry)

        # Handle collisions for same target name
        if new_rel in seen_targets:
            seen_targets[new_rel] += 1
            base, ext = new_rel.rsplit(".", 1)
            new_rel = f"{base}__{seen_targets[new_rel]}.{ext}"
        else:
            seen_targets[new_rel] = 1

        new_path = FIXTURE_DIR / new_rel

        host = old_rel.split("/")[0]
        index_entry = {
            "file": new_rel,
            "host": host,
            "method": file_entry["method"],
            "path": file_entry["path"],
            "params": file_entry.get("params", ""),
            "status": file_entry["status"],
            "description": description,
        }

        renames.append((old_path, new_path, index_entry))

    # Preview
    print(f"Renaming {len(renames)} files:\n")
    for old, new, _ in renames:
        old_rel = old.relative_to(FIXTURE_DIR)
        new_rel = new.relative_to(FIXTURE_DIR)
        print(f"  {old_rel}")
        print(f"    -> {new_rel}")
        print()

    # Execute renames
    for old_path, new_path, _ in renames:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))

    # Write new index
    index = [entry for _, _, entry in renames]
    index_path = FIXTURE_DIR / "index.json"
    index_path.write_text(json.dumps(index, indent=2))
    print(f"\nWrote {index_path} with {len(index)} entries")

    # Clean up empty host directories and old meta files
    for host_dir in FIXTURE_DIR.iterdir():
        if host_dir.is_dir() and host_dir.name.startswith("api."):
            remaining = list(host_dir.iterdir())
            if not remaining:
                host_dir.rmdir()
                print(f"Removed empty directory: {host_dir.name}")
            else:
                print(f"WARNING: {host_dir.name} still has {len(remaining)} files")

    # Remove old _meta.json and _anonymization_map.json (keep in raw_responses)
    for old_file in ["_meta.json", "_anonymization_map.json"]:
        p = FIXTURE_DIR / old_file
        if p.exists():
            p.unlink()
            print(f"Removed {old_file}")

    print("\nDone!")


if __name__ == "__main__":
    main()
