# Known Issues

Real issues found while building this feature and intentionally left unfixed.

## KI-001: An unrecognized late-cancel variant reads as cancelled, unlike the known `LateCancelled`

Status: open
Recorded: 2026-10-30 (161)
Source: ship-challenge
Reason not fixed now: accepted-limitation
Affected files:
- src/otf_api/models/bookings/bookings.py

Issue:
The known `LateCancelled` status counts as active, so it blocks rebooking and stays in `get_bookings`. A new or respelled variant such as `"Late cancelled"` carries `cancelledDate`, so `Booking.state` reads it as cancelled: hidden by default and rebookable.

Why deferred:
It needs OTF to respell or add a late-cancel status, and nothing on record shows that happening. The only local fix is a text heuristic on the status. The record stays reachable with `exclude_cancelled=False`, and the server decides the rebooking.

Recommended follow-up:
If OTF adds such a status, add it to `BookingStatus` with a deliberate state in `Booking.state`. `test_every_booking_status_member_has_a_decided_state` forces that choice.

Acceptance criteria:
- The new status behaves the same as `LateCancelled`, or differs by a recorded choice.

## KI-002: `get_bookings(status=<unrecognized>)` can return nothing with default flags

Status: open
Recorded: 2026-10-30 (161)
Source: ship-challenge
Reason not fixed now: accepted-limitation
Affected files:
- src/otf_api/api/bookings/booking_api.py

Issue:
If a caller passes back an unrecognized status and those records carry `cancelledDate` or `checkedInDate`, the default `exclude_cancelled=True` and `exclude_checkedin=True` remove everything the caller asked for, with no signal. `status=BookingStatus.CheckedIn` with default flags already behaves this way on the default branch.

Why deferred:
Skipping the exclusions whenever `status` is given would change results for known statuses, which D4 leaves alone. It needs a new OTF status and a caller filtering on it by name, and passing the flag as `False` avoids it.

Recommended follow-up:
If the known-status behavior is ever treated as a bug, skip both exclusions whenever `status` is given and delete the `Cancelled` guard, which fixes this case too.

Acceptance criteria:
- `get_bookings(status=X)` returns the records with status `X` under default flags, for known and unrecognized `X`.
