---
name: exceptions-optional-fields
description: OtfRequestError.response/.request are typed non-Optional but code sometimes passes None
metadata:
  type: project
---

<!-- 2026-09-05 -->
`src/otf_api/exceptions.py`'s `OtfRequestError` declares `response: "Response"` and
`request: "Request"` as non-Optional class attributes, but at least one call site
(`member_api.py`'s IDOR check, added 2026-09) passes `response=None, request=None`
with `# type: ignore[arg-type]` to suppress the mismatch.

**Why it matters:** `docs/guides/error-handling.md` documents catching `OtfRequestError`
generically and accessing `e.request.method` / `e.request.url` — that crashes with
`AttributeError` on a None request. `_sanitize_request()` already null-checks
`request is None`, showing the author knew this could happen but didn't update the
type annotation to `Request | None`.

**How to apply:** When reviewing new `raise exc.OtfRequestError(...)` call sites, check
whether `response`/`request` are being passed as `None`. If so, flag it — either the
field types need to become `Optional`, or the call site needs a real request/response
object. Don't let `# type: ignore[arg-type]` on these two fields pass silently.
