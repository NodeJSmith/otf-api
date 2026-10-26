# REVIEW.md — src/otf_api/

## v1 vs v2 Identifiers
`class_uuid`/`class_id` and `booking_uuid`/`booking_id` name the same objects in different
API versions, and the wrong one can 404 (e.g. a `class_uuid` passed to `book_class_new`).
For each changed call site, which identifier does it pass, and which version's endpoint
receives it? Trace it to the client method in `src/otf_api/api/bookings/booking_client.py`
(`default_request` is v1, `classes_request` is v2), not just the parameter name.

## v1/v2 Sibling Parity
Most booking operations exist as a v1/v2 pair (`book_class`/`book_class_new`,
`cancel_booking`/`cancel_booking_new`, `get_booking_from_class`/`..._new`). When one changes,
does its twin get the same change, and does each `isinstance(..., BookingV2)` branch return
rather than fall through into the other version's code?

## Path Identifier Validation
For each `*Client` method the diff adds or changes, list every value interpolated into the
URL path and where it was constrained: `validate_identifier` (`src/otf_api/api/utils.py`) or
an enum conversion upstream, like `TrendType` in `TrendApi`. Does any caller-supplied value
reach the path unconstrained?

## Eventual Consistency
Booking list endpoints (`get_bookings`, `get_bookings_new`) lag behind book/cancel calls, and
the mutation response is authoritative. Does any changed path read a list endpoint to verify
a mutation it just made, or to gate one, like `book_class`'s already-booked check or
`check_for_booking_conflicts`, where a stale entry would give the wrong answer?

## Cache Invalidation
Client getters are memoized for 10 minutes (`src/otf_api/cache.py`; tags like
`performance_summary`, `member_detail`). Does any new or changed mutation leave a cached read
of the thing it changed, or does it evict that tag the way `put_member_name` does?

## Unknown Upstream Values
`src/otf_api/models/base.py`'s `OtfItemBase` ignores unknown fields, but an enum-typed field
still rejects a value OTF adds later. For each new or changed enum field, what happens to the
whole record (and the list it's in) when the API returns a value the enum doesn't define?
