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

otf = Otf()

# Member info is loaded lazily on first access
print(f"Welcome, {otf.member.first_name}!")
print(f"Home studio: {otf.home_studio.name}")

# Get upcoming classes at your home studio
classes = otf.bookings.get_classes()
for otf_class in classes[:5]:
    print(f"  {otf_class.name} - {otf_class.starts_at}")
```

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
otf.bookings.cancel_booking(bookings[0])
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

## Next Steps

- **[Booking Guide](../guides/bookings.md)** — detailed class search, filtering, and booking workflows
- **[Workouts Guide](../guides/workouts.md)** — workout history, telemetry, and performance data
- **[Studios Guide](../guides/studios.md)** — studio search and favorites management
- **[API Reference](../reference/index.md)** — complete reference for all classes and methods
