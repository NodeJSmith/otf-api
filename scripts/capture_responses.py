"""Capture raw API responses from every read-only OTF endpoint.

Saves raw JSON responses to a structured directory for use as test fixtures
and for building the anonymization pipeline.

Usage:
    OTF_EMAIL=... OTF_PASSWORD=... uv run python scripts/capture_responses.py [output_dir]

Output structure:
    output_dir/
        api.orangetheory.co/
            member--members--{uuid}--bookings.json
            ...
        api.orangetheory.io/
            v1--classes.json
            v1--bookings--me.json
            ...
        api.yuzu.orangetheory.com/
            v1--physVars--maxHr--history.json
            ...
        _meta.json   (capture metadata: timestamp, endpoints hit, errors)
"""

import json
import sys
import time
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import pendulum

from otf_api import Otf
from otf_api.models.workouts import ChallengeCategory, EquipmentType, StatsTime

LOGGER = getLogger(__name__)

RESPONSE_LOG: list[dict[str, Any]] = []


def _slugify_path(url_path: str) -> str:
    """Turn a URL path into a safe filename, e.g. /v1/classes -> v1--classes."""
    cleaned = url_path.strip("/")
    return cleaned.replace("/", "--") + ".json"


def _response_hook(response: httpx.Response) -> None:
    """httpx event hook — captures every response before the library processes it."""
    response.read()

    parsed = urlparse(str(response.request.url))
    host = parsed.hostname or "unknown"
    filename = _slugify_path(parsed.path)
    params = parsed.query

    try:
        body = response.json()
    except Exception:
        body = {"_raw_text": response.text}

    RESPONSE_LOG.append({
        "host": host,
        "method": str(response.request.method),
        "path": parsed.path,
        "params": params,
        "status": response.status_code,
        "filename": filename,
        "body": body,
    })


def save_responses(output_dir: Path) -> dict[str, Any]:
    """Write all captured responses to disk, organized by host."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    seen_files: dict[str, int] = {}

    for entry in RESPONSE_LOG:
        host_dir = output_dir / entry["host"]
        host_dir.mkdir(exist_ok=True)

        filename = entry["filename"]
        if entry["params"]:
            base = filename.rsplit(".json", 1)[0]
            filename = f"{base}___{entry['params']}.json"

        key = f"{entry['host']}/{filename}"
        if key in seen_files:
            seen_files[key] += 1
            base = filename.rsplit(".json", 1)[0]
            filename = f"{base}___{seen_files[key]}.json"
        else:
            seen_files[key] = 1

        filepath = host_dir / filename
        filepath.write_text(json.dumps(entry["body"], indent=2, default=str))

        saved.append({
            "file": str(filepath.relative_to(output_dir)),
            "method": entry["method"],
            "path": entry["path"],
            "params": entry["params"],
            "status": entry["status"],
        })

    return {"saved": saved, "total": len(saved)}


def capture_all(otf: Otf) -> list[dict[str, str]]:
    """Call every read-only endpoint and return a log of what was called."""
    results = []

    def _call(name: str, fn, *args, **kwargs) -> Any:
        try:
            start = time.monotonic()
            result = fn(*args, **kwargs)
            elapsed = time.monotonic() - start
            results.append({"endpoint": name, "status": "ok", "elapsed": f"{elapsed:.2f}s"})
            return result
        except Exception as e:
            results.append({"endpoint": name, "status": "error", "error": f"{type(e).__name__}: {e}"})
            return None

    # -- Member (needed first for UUIDs) --
    member = _call("members.get_member_detail", otf.members.get_member_detail)
    _call("members.get_member_membership", otf.members.get_member_membership)
    _call("members.get_member_purchases", otf.members.get_member_purchases)
    _call("members.get_sms_notification_settings", otf.members.get_sms_notification_settings)
    _call("members.get_email_notification_settings", otf.members.get_email_notification_settings)

    # -- Studios --
    _call("studios.get_studio_detail", otf.studios.get_studio_detail)
    _call("studios.search_studios_by_geo", otf.studios.search_studios_by_geo)
    _call("studios.get_favorite_studios", otf.studios.get_favorite_studios)
    _call("studios.get_studio_services", otf.studios.get_studio_services)

    # -- Bookings --
    _call("bookings.get_classes", otf.bookings.get_classes)
    _call("bookings.get_bookings", otf.bookings.get_bookings)
    bookings_new = _call(
        "bookings.get_bookings_new",
        otf.bookings.get_bookings_new,
        pendulum.today().subtract(months=2),
    )

    # -- Workouts --
    _call("workouts.get_body_composition_list", otf.workouts.get_body_composition_list)
    _call("workouts.get_challenge_tracker", otf.workouts.get_challenge_tracker)
    _call("workouts.get_member_lifetime_stats_in_studio", otf.workouts.get_member_lifetime_stats_in_studio)
    _call(
        "workouts.get_member_lifetime_stats_in_studio (ThisMonth)",
        otf.workouts.get_member_lifetime_stats_in_studio,
        StatsTime.ThisMonth,
    )
    _call("workouts.get_member_lifetime_stats_out_of_studio", otf.workouts.get_member_lifetime_stats_out_of_studio)
    _call("workouts.get_out_of_studio_workout_history", otf.workouts.get_out_of_studio_workout_history)
    _call("workouts.get_hr_history", otf.workouts.get_hr_history)

    for et in EquipmentType:
        _call(f"workouts.get_benchmarks_by_equipment({et.name})", otf.workouts.get_benchmarks_by_equipment, et)

    for ct in ChallengeCategory:
        _call(
            f"workouts.get_benchmarks_by_challenge_category({ct.name})",
            otf.workouts.get_benchmarks_by_challenge_category,
            ct.value,
        )

    _call(
        "workouts.get_challenge_tracker_detail(DriTri)",
        otf.workouts.get_challenge_tracker_detail,
        ChallengeCategory.DriTri.value,
    )

    # -- Workouts that need a booking/performance_summary_id --
    perf_summary_id = None
    if bookings_new:
        for b in bookings_new:
            if b.workout and b.workout.performance_summary_id:
                perf_summary_id = b.workout.performance_summary_id
                break

    if perf_summary_id:
        _call("workouts.get_telemetry", otf.workouts.get_telemetry, perf_summary_id)

    workouts = _call("workouts.get_workouts", otf.workouts.get_workouts)

    return results


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fixtures/raw_responses")

    print(f"Output directory: {output_dir.resolve()}")
    print("Authenticating...")

    otf = Otf()

    session = otf.bookings.client.client.session
    existing_hooks = session.event_hooks.get("response", [])
    existing_hooks.append(_response_hook)
    session.event_hooks["response"] = existing_hooks

    print("Capturing responses from all read-only endpoints...\n")
    endpoint_results = capture_all(otf)

    print("\n--- Endpoint Results ---")
    for r in endpoint_results:
        status = "OK" if r["status"] == "ok" else f"FAIL: {r.get('error', 'unknown')}"
        elapsed = f" ({r['elapsed']})" if "elapsed" in r else ""
        print(f"  {r['endpoint']}: {status}{elapsed}")

    print(f"\nSaving {len(RESPONSE_LOG)} raw HTTP responses...")
    save_result = save_responses(output_dir)

    meta = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "total_http_responses": save_result["total"],
        "endpoints_called": len(endpoint_results),
        "endpoints_ok": sum(1 for r in endpoint_results if r["status"] == "ok"),
        "endpoints_failed": sum(1 for r in endpoint_results if r["status"] != "ok"),
        "endpoint_details": endpoint_results,
        "files": save_result["saved"],
    }

    meta_path = output_dir / "_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"\nDone! {save_result['total']} responses saved to {output_dir.resolve()}")
    print(f"Metadata: {meta_path}")

    ok = meta["endpoints_ok"]
    fail = meta["endpoints_failed"]
    print(f"\nSummary: {ok} endpoints succeeded, {fail} failed")

    if fail > 0:
        print("\nFailed endpoints:")
        for r in endpoint_results:
            if r["status"] != "ok":
                print(f"  - {r['endpoint']}: {r.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
