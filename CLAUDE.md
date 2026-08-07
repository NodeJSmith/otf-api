# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python library for the OrangeTheory Fitness API. Provides typed clients for bookings, member data, studios, and workouts, built on Pydantic v2, httpx, and AWS Cognito authentication.

## Development Setup

```bash
uv sync          # install all dependencies (dev group included by default)
```

## Common Commands

```bash
uv run pytest                          # run tests (requires real OTF credentials)
uv run pre-commit run --all-files      # lint + format (ruff, codespell, etc.)
uv run ruff check --fix --show-fixes   # lint only
uv run ruff format                     # format only
uv build                               # build wheel and sdist
uv run python scripts/generate_openapi.py  # generate OpenAPI schema from Pydantic models
uv run mkdocs serve                    # local docs dev server with live reload
uv run mkdocs build --strict           # build docs and verify (fails on warnings)
```

## Testing

Tests require real OrangeTheory credentials. Set `OTF_EMAIL` and `OTF_PASSWORD` environment variables before running pytest.

## Code Style

- **Line length**: 120 (configured in `ruff.toml`)
- **Docstrings**: Google-style
- **Quotes**: Double quotes
- **Indentation**: 4 spaces
- All Ruff rules are auto-fixable (`fixable = ["ALL"]`)
- Pre-commit hooks enforce ruff check, ruff format, codespell, and standard file hygiene

## Architecture Notes

- **Source layout**: `src/otf_api/` with sub-packages for `api/`, `auth/`, `models/`
- **Auth**: Cognito client ID, region, user pool ID, and identity pool ID are hardcoded in `auth/auth.py` (extracted from the OTF Android app)
- **Models**: All Pydantic models inherit from `OtfItemBase` which sets `extra="ignore"` to handle upstream API schema changes gracefully
- **Caching**: Disk-based response caching via `diskcache`, persists across sessions
- **Logging**: Auto-initialized on module import via `coloredlogs`; controlled by `OTF_LOG_LEVEL` env var (default: INFO)

## API Versioning and Dual Endpoints

OTF has multiple API surfaces that return overlapping but structurally different data. Understanding which is which is critical before making changes.

### V1 ("member" API) vs V2 ("classes" API)

| Concept | V1 | V2 |
|---|---|---|
| Base URL | `api.orangetheory.co` | `api.orangetheory.io` |
| Client method | `default_request()` | `classes_request()` |
| Booking model | `Booking` | `BookingV2` |
| Booking ID field | `booking_uuid` (from `classBookingUUId`) | `booking_id` |
| Class ID field | `class_uuid` | `class_id` |
| Cancel endpoint | `DELETE /member/members/{uuid}/bookings/{booking_uuid}` | `DELETE /v1/bookings/me/{booking_id}` |
| Book endpoint | `PUT /member/members/{uuid}/bookings` (takes `class_uuid`) | `POST /v1/bookings/me` (takes `class_id`) |
| Get bookings | `GET /member/members/{uuid}/bookings` → `list[Booking]` | `GET /v1/bookings/me` → `list[BookingV2]` |

### Key gotchas

- **`class_uuid` ≠ `class_id`**: These are different identifiers for the same class. `OtfClass` has both fields. Passing a `class_uuid` to `book_class_new` (v2) will 404.
- **`booking_uuid` ≠ `booking_id`**: Different identifiers for the same booking. The v1 and v2 APIs may or may not accept each other's IDs — behavior is inconsistent and undocumented.
- **Eventual consistency**: The booking list endpoints (`get_bookings`, `get_bookings_new`) are eventually consistent. A cancel or book call returns success immediately, but the listing endpoints may still show stale status for a short period. The cancel/book response itself is authoritative — don't re-fetch to "verify" immediately after a mutation.
- **Cross-version booking visibility**: A booking made via `book_class` (v1) may not appear in `get_bookings_new` (v2) immediately, and vice versa. Both endpoints eventually converge — the same bookings appear in both with different IDs (`booking_uuid` vs `booking_id`).
- **Studio data varies by endpoint**: The v1 bookings endpoint returns a minimal studio object. `get_classes` and `get_bookings` enrich it by fetching full `StudioDetail` via threaded calls to `/mobile/v1/studios/{uuid}`.
- **`OtfClass` comes from the classes endpoint, not the bookings endpoint**: It's enriched with studio data post-fetch. The raw API response has a different studio shape than what the model exposes.

### Gateway API ("consumer-mobile" / trends)

A third API surface added in app v5.6.0, serving workout trends data.

| Concept | Gateway |
|---|---|
| Base URL | `api.gateway.orangetheory.com` |
| Client method | `gateway_request()` |
| Endpoints | `GET /consumer-mobile/v1/users/me/workout-stats/{statsKey}`, `GET /consumer-mobile/v1/users/me/workout-stats/preview` |
| Auth | Same Cognito bearer token as v1/v2 |
| Response format | snake_case JSON (unlike the camelCase used by some v1/v2 endpoints) |
| Available stat keys | `splat_points`, `average_hr`, `peak_hr`, `tread_top_speed`, `rower_500m_split_time`, `rower_top_power` |

### Two-layer architecture (Client → Api)

Each domain has a `*Client` (raw HTTP, returns dicts) and a `*Api` (business logic, returns models):

- `BookingClient` / `BookingApi` — raw HTTP calls vs typed booking operations
- `StudioClient` / `StudioApi` — raw HTTP calls vs typed studio operations
- `WorkoutClient` / `WorkoutApi` — raw HTTP calls vs typed workout operations
- `MemberClient` / `MemberApi` — raw HTTP calls vs typed member operations
- `TrendClient` / `TrendApi` — raw HTTP calls vs typed workout trends/stats operations

The `*Client` classes are internal; the `*Api` classes are what users interact with via `Otf.bookings`, `Otf.studios`, `Otf.trends`, etc.

### Testing with fixtures

The fixture-based test suite (`tests/`) uses `respx` to mock HTTP — no credentials needed. Fixtures live in `fixtures/anonymized/`.

## Git Workflow

- Feature branches for new work
- Versioning and release PRs managed via `release-please`
- CI runs tests on Python 3.11 and 3.12, plus pre-commit checks
- Releases created through the release-please workflow; published to PyPI via trusted publishing
