---
name: identifier-validation-convention
description: otf-api's convention for validating URL-path-segment identifiers (booking_uuid, class_uuid, studio_uuid, performance_summary_id) before interpolating into request paths
metadata:
  type: project
---

<!-- 2026-09-05 -->
As of commit fb352e3 ("client-side security hardening against API weaknesses"), the established
pattern is: any identifier interpolated into an HTTP path segment must pass through
`otf_api.api.utils.validate_identifier()` (rejects path separators, `..`, null bytes, whitespace,
percent-encoding) before being used to build a URL. This is applied either directly in the
`*Client` class (e.g. `StudioClient.get_studio_detail`, `WorkoutClient.get_performance_summary`)
or via the shared `utils.get_booking_uuid`/`get_booking_id`/`get_class_uuid`/`get_class_id` helpers
that `*Api` classes call before delegating to the client.

**Known gap as of fb352e3 (flagged, not yet fixed):** `BookingClient.get_booking` interpolates
`booking_uuid` into a path with no validation, and `BookingApi.get_booking` (a public,
directly-callable method) does not call `utils.get_booking_uuid` before forwarding. Check this
specific method when reviewing future diffs — if still unpatched, it's a real gap, not a false
positive.

**Also flagged in the same diff:** `TrendClient.get_workout_stats` closes the same class of gap
by narrowing `TrendApi.get_workout_stats`'s `trend_type` param from `TrendType | str` to
`TrendType` instead of calling `validate_identifier` — a different (breaking) technique for the
same problem. Worth checking whether this was reconciled to the `validate_identifier` pattern or
left as an enum-only breaking change.

**Also flagged:** `OtfRequestError.response`/`.request` are typed non-Optional and one existing
catch site (`booking_api.py` `post_class_rating`, `except OtfRequestError as e: e.response.status_code`)
relies on that being true. `MemberApi.get_member_detail`'s new IDOR guard raises
`OtfRequestError(response=None, request=None)`, violating that invariant. Check whether the type
was ever changed to `Response | None` / `Request | None` with consumers updated, or whether this
call site was given a synthetic Response/Request instead.
