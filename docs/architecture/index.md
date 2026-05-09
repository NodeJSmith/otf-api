# Architecture Overview

The `otf-api` library is organized into four layers: API clients, models, authentication, and caching.

## Layer Diagram

```
┌─────────────────────────────────────────────┐
│              Your Application                │
├─────────────────────────────────────────────┤
│         Otf (main client facade)            │
├──────────┬──────────┬──────────┬────────────┤
│ Bookings │ Members  │ Studios  │ Workouts   │
├──────────┴──────────┴──────────┴────────────┤
│         OtfClient (HTTP layer)              │
├─────────────────────┬───────────────────────┤
│   HttpxCognitoAuth  │     OtfCache          │
│   (request signing) │  (disk persistence)   │
├─────────────────────┴───────────────────────┤
│         OtfCognito (AWS Cognito)            │
└─────────────────────────────────────────────┘
```

## API Domain Structure

The `Otf` class is the entry point. It exposes four domain-specific API objects as attributes:

| Property | Class | Responsibility |
|----------|-------|---------------|
| `otf.bookings` | `BookingApi` | Book/cancel classes, list upcoming bookings |
| `otf.members` | `MemberApi` | Member profile, stats, favorite studios |
| `otf.studios` | `StudioApi` | Studio search, details, class schedules |
| `otf.workouts` | `WorkoutApi` | Workout history, performance summaries |

Each API class receives a shared `OtfClient` instance that handles HTTP transport with automatic authentication.

## Model Hierarchy

All response models inherit from `OtfItemBase`:

```python
class OtfItemBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
```

The `extra="ignore"` setting is deliberate — the upstream OTF API frequently adds new fields without notice. Ignoring unknown fields prevents breakage when the API schema changes.

### ApiMixin

Models that support actions (e.g., cancelling a booking from the booking object itself) use `ApiMixin`. This mixin holds a reference to the `Otf` client, enabling method calls like:

```python
booking.cancel()  # calls otf.bookings.cancel_booking internally
```

The API reference is injected by the API layer when models are returned from queries.

## Authentication Flow

Authentication is handled by two classes:

- **`OtfCognito`** — extends `pycognito.Cognito` to add device key support required by the OTF Cognito pool. Manages SRP login, token refresh, and device confirmation.
- **`HttpxCognitoAuth`** — an `httpx.Auth` implementation that attaches the ID token to every request and triggers refresh when tokens expire. For endpoints requiring AWS SigV4 signing, it fetches temporary credentials from the Cognito Identity Pool.

The `OtfUser` class wraps `OtfCognito` and provides a clean interface for credential resolution (direct, env vars, or interactive prompt).

## Caching

`OtfCache` (a `diskcache.Cache` subclass) persists two categories of data:

| Tag | Contents | Expiration |
|-----|----------|------------|
| `token` | Access, ID, and refresh tokens | Matches token TTL |
| `device` | Device key, group key, password | No expiration |

The cache directory is platform-specific (via `platformdirs`) and versioned by library major version to avoid cross-version conflicts.

## Module Map

| Package | Purpose |
|---------|---------|
| `otf_api/api/` | Domain API classes (`BookingApi`, `MemberApi`, `StudioApi`, `WorkoutApi`) and the HTTP client |
| `otf_api/models/` | Pydantic response models, base classes, and mixins |
| `otf_api/auth/` | Cognito authentication, HTTPX auth handler, credential utilities |
| `otf_api/cache.py` | Disk cache wrapper for tokens and device data |
| `otf_api/exceptions.py` | Exception hierarchy for all library errors |

!!! note
    The Cognito configuration (client ID, pool ID, region) is extracted from the official OrangeTheory Android app and hardcoded in the auth module. These values are not user-configurable.
