# otf-api

**Python client for the OrangeTheory Fitness API.**

A fully typed Python library for interacting with the OrangeTheory Fitness API. Manage class bookings, retrieve workout history with heart-rate telemetry, search studios, and access member data — all with automatic AWS Cognito authentication handled behind the scenes.

## Installation

```bash
pip install otf-api
```

## Quick Example

```python
from otf_api import Otf

otf = Otf()

# Get upcoming classes at your home studio
classes = otf.bookings.get_classes()
for otf_class in classes[:5]:
    print(f"{otf_class.name} - {otf_class.starts_at}")

# Book a class
otf.bookings.book_class(classes[0])
```

## Features

- **Class booking** — search available classes, book, cancel, and check waitlist status
- **Workout history** — retrieve past workouts with performance summaries and heart-rate telemetry
- **Studio search** — find studios by location, manage favorites
- **Challenge tracking** — view benchmarks, challenge participation, and personal records
- **Member data** — profile details, memberships, and purchase history
- **Automatic authentication** — AWS Cognito auth with token caching across sessions
- **Fully typed** — Pydantic v2 models for all API responses

## Documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting Started](getting-started/index.md)**

    Installation, authentication, and your first API call.

- :material-book-open-variant: **[Guides](guides/index.md)**

    In-depth guides for bookings, workouts, studios, and members.

- :material-cog: **[Architecture](architecture/index.md)**

    Internal design, caching, and extension points.

- :material-api: **[API Reference](reference/otf_api/index.md)**

    Auto-generated reference for all modules and classes.

</div>
