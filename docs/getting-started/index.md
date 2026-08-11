# Getting Started

This guide walks you through installing otf-api, authenticating, and making your first API calls.

## Prerequisites

- **Python 3.11+**
- **Active OrangeTheory Fitness membership** — the API uses your member credentials

## Installation

```bash
pip install otf-api
```

## Authentication

The library authenticates via AWS Cognito using your OrangeTheory account credentials. There are three ways to provide them:

### Environment Variables (Recommended)

Set `OTF_EMAIL` and `OTF_PASSWORD` in your environment:

```bash
export OTF_EMAIL="your.email@example.com"
export OTF_PASSWORD="your-password"
```

Then initialize without arguments:

```python
from otf_api import Otf

otf = Otf()
```

### Direct Credentials

Pass credentials explicitly via `OtfUser`:

```python
from otf_api import Otf, OtfUser

otf = Otf(user=OtfUser(username="your.email@example.com", password="your-password"))
```

### Interactive Prompt

If no credentials are found in the environment, the library prompts you interactively:

```python
from otf_api import Otf

otf = Otf()  # Prompts for email and password if OTF_EMAIL/OTF_PASSWORD are not set
```

!!! tip "Token Caching"
    After the first successful authentication, tokens are cached to disk. Subsequent runs reuse the cached tokens and refresh them automatically — you won't need to re-enter credentials until the refresh token expires.

## Your First API Call

```python
from otf_api import Otf

with Otf() as otf:
    # Member info is loaded lazily on first access
    print(f"Welcome, {otf.member.first_name}!")
    print(f"Home studio: {otf.home_studio.name}")

    # Get upcoming classes at your home studio
    classes = otf.bookings.get_classes()
    for otf_class in classes[:5]:
        print(f"  {otf_class.name} - {otf_class.starts_at}")
```

`Otf` supports context management (`with` statement) for automatic cleanup of HTTP resources. You can also call `otf.close()` manually, or let the `atexit` handler clean up at process exit.

## Exploring the API

The `Otf` client organizes functionality into four domain APIs:

### `otf.bookings` — Class Scheduling

Search for available classes, view your upcoming bookings, book, and cancel:

```python
# Get classes at your home studio
classes = otf.bookings.get_classes()

# Get your upcoming bookings
bookings = otf.bookings.get_bookings_new()

# Book a class
otf.bookings.book_class(classes[0])

# Cancel a booking
otf.bookings.cancel_booking_new(bookings[0])
```

### `otf.workouts` — Workout History

Retrieve past workouts with performance summaries, heart-rate telemetry, and benchmark data:

```python
# Get recent workouts (last 30 days by default)
workouts = otf.workouts.get_workouts()

# Get challenge/benchmark results
benchmarks = otf.workouts.get_benchmarks()

# Get body composition data
body_comp = otf.workouts.get_body_composition_list()
```

### `otf.studios` — Studio Search

Find studios by location and manage your favorites:

```python
# Search studios near a location
studios = otf.studios.search_studios_by_geo(latitude=40.7128, longitude=-74.0060)

# Get your favorite studios
favorites = otf.studios.get_favorite_studios()
```

### `otf.members` — Profile and Membership

Access your profile details, membership info, and purchase history:

```python
# Get full member details
member = otf.members.get_member_detail()

# Get membership info
membership = otf.members.get_member_membership()

# Get purchase history
purchases = otf.members.get_member_purchases()
```

!!! warning "Rate Limiting"
    The OrangeTheory API is not a public API. Be respectful with request frequency — avoid tight loops or polling. The library caches responses where appropriate to minimize unnecessary requests.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OTF_EMAIL` | OrangeTheory Fitness account email address |
| `OTF_PASSWORD` | OrangeTheory Fitness account password |
| `OTF_LOG_LEVEL` | Logging verbosity (default: `INFO`) |
| `OTF_ANONYMIZE_RESPONSES` | Set to `true` to capture and anonymize all API responses to disk |
| `OTF_ANONYMIZE_OUTPUT_DIR` | Override the anonymized capture output directory |
| `OTF_ANONYMIZE_SEED` | Integer seed for reproducible anonymization (auto-derived from member UUID if unset) |
| `OTF_ANONYMIZE_STRICTNESS` | Strictness level: `permissive`, `mask` (default), or `drop` |

### Cache Management

The library caches authentication tokens and device registration data to disk using [`diskcache`](https://grantjenks.com/docs/diskcache/). The cache directory is determined by [`platformdirs`](https://platformdirs.readthedocs.io/en/latest/) and versioned by major library version.

**Typical locations:**

- Linux: `~/.cache/otf-api/v0/`
- macOS: `~/Library/Caches/otf-api/v0/`
- Windows: `C:\Users\<user>\AppData\Local\otf-api\Cache\v0\`

**Clearing the cache:**

```python
from otf_api.cache import clear_cache

# Clear everything (tokens + device data)
clear_cache()
```

!!! tip "Selective cache clearing"
    ```python
    from otf_api.cache import get_cache

    cache = get_cache()
    cache.clear_tokens()       # Remove only auth tokens
    cache.clear_device_data()  # Remove only device registration
    ```

## Next Steps

- **[Booking Guide](../guides/bookings.md)** — detailed class search, filtering, and booking workflows
- **[Workouts Guide](../guides/workouts.md)** — workout history, telemetry, and performance data
- **[Studios Guide](../guides/studios.md)** — studio search and favorites management
- **[API Reference](../reference/index.md)** — complete reference for all classes and methods
