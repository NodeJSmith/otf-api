---
task_id: "T02"
title: "Export exception classes in public API"
status: "planned"
depends_on: []
implements: ["FR#10", "AC#7"]
---

## Summary
Add `__all__` to `exceptions.py` listing all 11 exception classes, and add exceptions to the top-level `__init__.py` exports. This makes `from otf_api.exceptions import ConflictingBookingError` a documented, supported import path and ensures the API reference includes the exception hierarchy.

## Prompt
Make two source code changes:

### 1. Add `__all__` to `src/otf_api/exceptions.py`
Add an `__all__` list at the top of the file (after imports) containing all 11 exception classes:
```python
__all__ = [
    "OtfError",
    "OtfRequestError",
    "RetryableOtfRequestError",
    "BookingError",
    "AlreadyBookedError",
    "ConflictingBookingError",
    "BookingAlreadyCancelledError",
    "OutsideSchedulingWindowError",
    "ResourceNotFoundError",
    "AlreadyRatedError",
    "ClassNotRatableError",
]
```

### 2. Update `src/otf_api/__init__.py`
Add the exceptions module to the top-level `__all__`:
```python
__all__ = ["AnonymizeConfig", "Anonymizer", "Otf", "OtfUser", "exceptions", "models"]
```
Also add `from otf_api import exceptions` if not already present so the module is importable as `otf_api.exceptions`.

### 3. Verify
Confirm existing code still works — `examples/workout_examples.py` already imports `from otf_api.exceptions import AlreadyRatedError, ClassNotRatableError`. Run `uv run python -c "from otf_api.exceptions import ConflictingBookingError; print(ConflictingBookingError)"` to verify the import path works.

## Focus
- `src/otf_api/exceptions.py` has 11 exception classes. All already have docstrings — no docstring work needed.
- `src/otf_api/__init__.py` currently exports: `["AnonymizeConfig", "Anonymizer", "Otf", "OtfUser", "models"]`.
- There's also a `NoCredentialsError` in `src/otf_api/auth/auth.py` — this is NOT exported and should NOT be added here (it's internal to the auth flow).
- The `examples/workout_examples.py` already imports from `otf_api.exceptions` — adding `__all__` won't break this.

## Verify
- [ ] FR#10: `from otf_api.exceptions import OtfError, BookingError, ConflictingBookingError` succeeds in a Python REPL
- [ ] AC#7: All 11 exception classes are importable from `otf_api.exceptions` and `otf_api.exceptions.__all__` contains exactly 11 entries
