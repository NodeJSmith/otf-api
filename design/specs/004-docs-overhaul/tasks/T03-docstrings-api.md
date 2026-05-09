---
task_id: "T03"
title: "Add comprehensive docstrings to API classes"
status: "planned"
depends_on: []
implements: ["FR#14", "AC#2"]
---

## Summary
Fill all remaining docstring gaps on the public API classes: `Otf`, `BookingApi`, `MemberApi`, `StudioApi`, `WorkoutApi`, and auth classes. Every public method, property, and class must have a Google-style docstring with Args, Returns, and Raises sections where applicable. This ensures the auto-generated API reference is complete.

## Prompt
Add or improve Google-style docstrings across the API layer. Use the existing docstring patterns in the codebase as a template (see Focus section).

### Files to update (check each for missing docstrings):

**Main client:**
- `src/otf_api/api/api.py` — `Otf` class: fill `member_uuid`, `home_studio`, `home_studio_uuid` properties

**Booking API:**
- `src/otf_api/api/bookings/booking_api.py` — `BookingApi`: check all public methods

**Member API:**
- `src/otf_api/api/members/member_api.py` — `MemberApi`: check all public methods

**Studio API:**
- `src/otf_api/api/studios/studio_api.py` — `StudioApi`: check all public methods

**Workout API:**
- `src/otf_api/api/workouts/workout_api.py` — `WorkoutApi`: check all public methods

**Auth:**
- `src/otf_api/auth/auth.py` — `OtfCognito`: fill `access_token_expiration`, `tokens`, `device_metadata` properties; fill `login_with_password` method. `HttpxCognitoAuth`: fill `auth_flow`, `sign_httpx_request` methods.

**Utilities (public functions only):**
- `src/otf_api/api/utils.py` — fill `is_error_response`, `get_json_from_response`
- `src/otf_api/api/client.py` — fill `default_request` on `OtfClient`

### Docstring format
Follow the existing Google-style convention already in use:
```python
def method_name(self, param: str) -> ReturnType:
    """Brief one-line summary.

    Longer description if needed.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        OtfRequestError: When the API returns an error.
    """
```

Do NOT add docstrings to private methods (starting with `_`) unless they already have one.

## Focus
- Read `src/otf_api/api/bookings/booking_api.py` first — it has the best docstring examples to follow (uses Args, Returns, Note, Warning, Tip sections).
- The `Otf` class at `src/otf_api/api/api.py` has comprehensive class-level and method docstrings but 3 properties missing docstrings.
- Auth classes at `src/otf_api/auth/auth.py` have ~68% coverage — 5 methods/properties need docstrings.
- `src/otf_api/api/client.py` is mostly internal but `OtfClient` and `default_request` are used by the domain APIs.
- Do NOT touch `*_client.py` files in the domain directories (e.g., `booking_client.py`) — these are internal HTTP wrappers. Note: `src/otf_api/api/client.py` (the base `OtfClient` class) IS in scope — the constraint targets `booking_client.py`/`member_client.py`-style transport wrappers, not the base client.

## Verify
- [ ] FR#14: Every public method and property on `Otf`, `BookingApi`, `MemberApi`, `StudioApi`, `WorkoutApi`, `OtfCognito`, `HttpxCognitoAuth`, and `OtfClient` has a docstring
- [ ] AC#2: Running `python -c "import otf_api; help(otf_api.Otf.member_uuid)"` produces a docstring (spot check for previously undocumented properties)
