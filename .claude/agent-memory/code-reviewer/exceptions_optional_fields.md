---
name: exceptions-optional-fields
description: OtfRequestError.response/.request are typed non-Optional; historical None call-site no longer exists
metadata:
  type: project
---

<!-- 2026-09-05 (updated) -->
`src/otf_api/exceptions.py`'s `OtfRequestError` declares `response: httpx.Response` and
`request: httpx.Request` as non-Optional class attributes. An earlier note recorded a
`member_api.py` IDOR-check call site passing `response=None, request=None` with
`# type: ignore[arg-type]` — **verified stale as of 2026-09-05**: that call site was
refactored (commit `d792c91`, "address clean code review findings") to raise a plain
`ValueError` instead of `OtfRequestError`, so no current call site passes None for
these fields. Grepped all `OtfRequestError(`/`RetryableOtfRequestError(` call sites in
`src/` and `tests/` on that date — all pass real `httpx.Request`/`httpx.Response`
objects.

**Why it still matters:** `OtfRequestError.__init__` now (as of the same date) mutates
`self.response.request` and `self.original_exception.request` in place to redact
sensitive headers from any retained references. If a future call site ever reintroduces
`response=None` or `request=None`, this would crash with `AttributeError` before the
message even gets set. `_sanitize_request()` has no None-guard either.

**How to apply:** When reviewing new `raise exc.OtfRequestError(...)` call sites, check
whether `response`/`request` are ever `None`. If so, flag it — either the field types
need to become `Optional`, or the call site needs a real request/response object. Don't
trust this note's own history at face value either — re-verify against current
`src/otf_api/api/client.py` before citing it, since it has already gone stale once.
