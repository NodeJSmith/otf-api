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

**Resolved (as of 2026-09-05, branch `security/client-hardening`):** `TrendApi.get_workout_stats`
now does both — enforces `isinstance(trend_type, TrendType)` (raising `TypeError`, matching the
`get_booking_id`/`get_class_uuid`-style "Expected X or str" convention in `api/utils.py`) *and*
still runs `trend_type.value` through `utils.validate_identifier` before it reaches the client.
Reconciled, not a parallel technique.

**Resolved:** `OtfRequestError(response=None, request=None)` call site is gone — grep for
`response=None` / `request=None` across `src/otf_api` turns up nothing. `response`/`request`
stay typed non-Optional.

**New in the same hardening pass:** `OtfRequestError.__init__` now mutates the *caller-supplied*
`response`/`original_exception` objects in place (`self.response.request = sanitized_request`,
`self.original_exception.request = sanitized_request`) so that downstream code holding the same
reference (e.g. `anonymize/hooks.py`, which reads `response.request` for logging) doesn't see the
unsanitized request. This is a deliberate, load-bearing exception to the "never mutate existing
objects" rule — the leak isn't closed otherwise, since `self.request` alone doesn't cover
`response.request`/`original_exception.request`. Flag it as intentional if seen again, not a fresh
violation.

**Tooling gap:** `ruff.toml` excludes `tests/` entirely (`exclude = [..., "tests"]`), so
`ruff check .` / the `ruff-check` pre-commit hook never lints test files — unused imports,
missing annotations, etc. in `tests/` pass CI silently. Running `ruff check <path>` with an
explicit test file path bypasses the exclude and does catch these; use that when reviewing test
diffs in this repo, since the standard hook won't.
