---
task_id: "T06"
title: "Write domain-specific guides"
status: "planned"
depends_on: ["T01"]
implements: ["FR#6", "AC#6"]
---

## Summary
Write five domain-specific guide pages covering the library's main feature areas: bookings/classes, workouts/stats, studios, challenges/benchmarks, and members. Each guide provides explanatory prose with code examples showing common workflows. The existing example scripts in `examples/` are the primary source material.

## Prompt
Replace the placeholder guide pages with full content. For each guide, read the corresponding example script and the domain API class to extract accurate code patterns and method signatures.

### 1. `docs/guides/bookings.md` — Bookings & Classes
Source: `examples/class_bookings_examples.py` and `src/otf_api/api/bookings/booking_api.py`

Cover:
- Searching for available classes (`get_classes`)
- Filtering classes by day of week, time, class type, studio using `ClassFilter`
- Booking a class (`book_class`)
- Viewing your bookings (`get_bookings_new`)
- Cancelling a booking (`cancel_booking`)
- Rating a class and coach
- Handling booking conflicts and errors (link to error handling guide)

### 2. `docs/guides/workouts.md` — Workouts & Stats
Source: `examples/workout_examples.py` and `src/otf_api/api/workouts/workout_api.py`

Cover:
- Getting workout history (`get_workouts`)
- Viewing performance summaries
- Accessing telemetry data (heart rate zones, tread/rower data)
- Lifetime stats (`get_stats`)
- Body composition data
- Filtering workouts by date range

### 3. `docs/guides/studios.md` — Studios
Source: `examples/studio_examples.py` and `src/otf_api/api/studios/studio_api.py`

Cover:
- Searching for studios by location
- Getting studio details
- Managing favorite studios (add/remove)
- Studio services

### 4. `docs/guides/challenges.md` — Challenges & Benchmarks
Source: `examples/challenge_tracker_examples.py` and `src/otf_api/api/workouts/workout_api.py`

Cover:
- Viewing challenge tracker data
- Fitness benchmarks
- Challenge categories and types

### 5. `docs/guides/members.md` — Members
Source: `src/otf_api/api/members/member_api.py` (no example script exists for this)

Cover:
- Getting member details (`get_member_detail`)
- Viewing memberships and purchases
- Updating member name
- Notification settings (SMS and email)

### Writing guidelines
- Start each guide with a brief intro (2-3 sentences) explaining what the domain covers
- Show complete, runnable code examples (assume `otf = Otf()` is already initialized)
- Use admonition blocks (`!!! tip`, `!!! warning`, `!!! note`) for important callouts
- Link to the API reference for method details (use mkdocstrings cross-references like `[BookingApi][otf_api.api.bookings.booking_api.BookingApi]`)
- Each guide should be self-contained — a user reading only that guide should understand the domain

## Focus
- Read each example script carefully — they contain real API usage patterns and sample JSON output in docstrings.
- The bookings guide is the most complex — it has class filtering, booking flow, conflict handling, and ratings.
- The members guide has no example script — extract patterns from `member_api.py` docstrings.
- Be aware of the dual booking API: the guides should use the new `BookingV2`/`get_bookings_new` API. Mention the old API only in a note about backwards compatibility.
- `ClassFilter` is a powerful feature — give it a dedicated subsection in the bookings guide.
- Code examples must use actual method names from the source. Verify each one.

## Verify
- [ ] FR#6: Five guide pages exist covering bookings, workouts, studios, challenges, and members
- [ ] AC#6: Each of the five guides contains at least one complete code example with explanatory prose
