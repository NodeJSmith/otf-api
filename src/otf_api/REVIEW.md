# REVIEW.md — src/otf_api/

## v1 vs v2 Identifiers
`class_uuid`/`class_id` and `booking_uuid`/`booking_id` name the same objects in different
API versions, and the wrong one 404s. For each changed call site, which identifier does it
pass, and which version's endpoint receives it? Trace it through `src/otf_api/api/utils.py`'s
`get_class_*`/`get_booking_*` helpers, not just the parameter name.

## Path Identifier Validation
Does every new or changed `*Client` method that interpolates a caller-supplied value into a
URL path call `validate_identifier` (`src/otf_api/api/utils.py`) on it first? Values sent
in a JSON body or query params don't need it; does the change validate any of those anyway?

## Eventual Consistency
Booking list endpoints (`get_bookings`, `get_bookings_new`) lag behind book/cancel calls, and
the mutation response is authoritative. Does any changed path read a list endpoint to verify
a mutation it just made, or to decide whether a mutation is allowed (e.g. an "already booked"
pre-check) where a stale entry would give the wrong answer?

## Unknown Upstream Values
`src/otf_api/models/base.py`'s `OtfItemBase` ignores unknown fields, but an enum-typed field
still rejects a value OTF adds later. For each new or changed enum field, what happens to the
whole record (and the list it's in) when the API returns a value the enum doesn't define?
