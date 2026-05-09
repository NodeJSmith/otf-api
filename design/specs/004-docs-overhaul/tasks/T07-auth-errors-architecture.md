---
task_id: "T07"
title: "Write auth, error handling, and architecture guides"
status: "planned"
depends_on: ["T01", "T02"]
implements: ["FR#7", "FR#8", "FR#11", "AC#7", "AC#11", "AC#12"]
---

## Summary
Write three guide pages that address the most common user pain points: authentication setup and token management, error handling with the exception hierarchy, and an architecture overview explaining how the library is structured. These guides fill the biggest documentation gaps identified from GitHub issues.

## Prompt
Replace the placeholder pages with full content.

### 1. `docs/guides/authentication.md` — Authentication
Source: `src/otf_api/auth/auth.py`, `src/otf_api/auth/user.py`, `src/otf_api/cache.py`

Cover:
- **Credential setup**: Three methods (env vars, direct, prompt) — expand on the getting started guide with more detail
- **How authentication works**: High-level explanation of the Cognito flow (client ID, user pool — without exposing hardcoded values). Explain that the library handles token acquisition and refresh automatically.
- **Token caching**: `diskcache`-based caching persists tokens across sessions. Explain the cache directory location and how to clear it (`from otf_api.cache import clear_cache; clear_cache()`)
- **Device key management**: Brief explanation — the library registers a device key with Cognito to avoid re-authentication challenges
- **Token refresh**: Tokens expire and are refreshed automatically. Explain the lifecycle.
- **`OtfUser` class**: Detailed documentation of initialization options and what each field does
- **Troubleshooting auth issues**: Common problems (wrong credentials, expired tokens, cache corruption) with solutions. Link to main troubleshooting page.

### 2. `docs/guides/error-handling.md` — Error Handling
Source: `src/otf_api/exceptions.py`

Cover:
- **Exception hierarchy**: Visual tree showing inheritance:
  ```
  OtfError
  ├── OtfRequestError
  │   └── RetryableOtfRequestError
  ├── BookingError
  │   ├── AlreadyBookedError
  │   ├── ConflictingBookingError
  │   ├── BookingAlreadyCancelledError
  │   └── OutsideSchedulingWindowError
  ├── ResourceNotFoundError
  ├── AlreadyRatedError
  └── ClassNotRatableError
  ```
- **Each exception**: Description, common causes, and a code example showing how to catch it
- **Error handling patterns**: Show idiomatic try/except patterns for common operations (booking a class, cancelling, rating)
- **`OtfRequestError` details**: Explain the `original_exception`, `response`, and `request` attributes
- **`BookingError` details**: Explain the `booking_uuid` and `booking_id` attributes
- **Retry behavior**: Explain `RetryableOtfRequestError` and when automatic retries occur

Reference the `__all__` export from T02 — all exceptions should be importable from `otf_api.exceptions`.

### 3. `docs/architecture/index.md` — Architecture Overview
Source: `src/otf_api/api/api.py`, `src/otf_api/models/base.py`, the overall source structure

Cover:
- **High-level structure**: The library has four layers: API clients, models, authentication, and caching
- **API domain structure**: The `Otf` class exposes four sub-clients via properties: `bookings` (BookingApi), `members` (MemberApi), `studios` (StudioApi), `workouts` (WorkoutApi). Each sub-client handles one domain of the OTF API.
- **Model hierarchy**: All Pydantic models inherit from `OtfItemBase` (which sets `extra="ignore"` to handle upstream API changes). Some models also use `ApiMixin` for methods like `book_class()` and `cancel()` directly on model instances.
- **Authentication flow**: `OtfCognito` handles Cognito auth, `HttpxCognitoAuth` signs httpx requests. Token caching via `diskcache`.
- **Caching layer**: Disk-based response caching for tokens and device data.
- **Module map**: List each sub-package and its purpose (1-2 sentences each)

Keep this guide concise — it's an orientation document, not a deep dive. Link to the API reference for implementation details.

## Focus
- Auth is the biggest user pain point based on GitHub issues. The guide should address real confusion: "where do tokens go?", "why am I re-authenticating?", "what's a device key?"
- Read `src/otf_api/auth/auth.py` carefully — the Cognito client ID, region, user pool ID, and identity pool ID are hardcoded (extracted from the OTF Android app). Don't expose these values in the docs, but explain the approach.
- The exception hierarchy has clear inheritance — `BookingError` is a base for 4 booking-specific exceptions. Show this visually.
- `OtfRequestError` has custom `__init__` with `original_exception`, `response`, `request` attributes — these are useful for debugging and should be documented.
- The architecture overview should help a new reader understand where code lives without reading every file.
- T02 must complete before this task — the error handling guide references the exported exceptions.

## Verify
- [ ] FR#7: The auth guide covers env vars, direct credentials, OtfUser prompt, token caching, and device key management
- [ ] FR#8: The error handling guide documents all 11 exception classes with descriptions and common causes
- [ ] FR#11: The architecture overview explains the four-domain API structure, auth flow, and caching layer
- [ ] AC#7: The error handling guide shows import paths for all exceptions from `otf_api.exceptions`
- [ ] AC#11: The auth guide covers all three credential methods and explains token caching/refresh
- [ ] AC#12: The architecture overview names all four API sub-clients and explains the module structure
