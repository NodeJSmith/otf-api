---
task_id: "T04"
title: "Add comprehensive docstrings to models and enums"
status: "planned"
depends_on: []
implements: ["FR#14", "AC#2", "AC#3"]
---

## Summary
Fill all remaining docstring gaps on Pydantic model classes, enum classes, and model methods. Add `Field(description=...)` to fields that lack descriptions in user-facing models. This is the largest docstring task — covering ~80 classes and ~200 fields across the models sub-packages.

## Prompt
Add or improve docstrings and field descriptions across all model files. Work through each sub-package systematically.

### Booking models
- `src/otf_api/models/bookings/classes.py` — Add class docstrings to `OtfClass`, `Coach`, `BookingClass`, `Booking`. Add docstrings to undocumented properties (`day_of_week`, `has_availability`, `day_of_week_enum`). Add `Field(description=...)` to fields that lack it.
- `src/otf_api/models/bookings/bookings_v2.py` — Add class docstrings to `Rating`, `BookingV2Studio`, `BookingV2Class`, `BookingV2Workout`, `BookingV2`. Add property docstrings. Add field descriptions.
- `src/otf_api/models/bookings/enums.py` — Add class docstrings to `BookingStatus`, `DoW`, `ClassType`, and all `*ClassType` sub-enums. Add method docstrings to `priority()`, `get_case_insensitive()`, `get_standard_class_types()`, `get_tread_strength_class_types()`.
- `src/otf_api/models/bookings/filters.py` — already complete, verify only.
- `src/otf_api/models/bookings/ratings.py` — already complete, verify only.

### Member models
- `src/otf_api/models/members/member_detail.py` — Add class docstrings to `MemberProfile`, `MemberClassSummary`, `MemberDetail`. Add field descriptions.
- `src/otf_api/models/members/member_membership.py` — Add class docstring to `MemberMembership`. Add field descriptions.
- `src/otf_api/models/members/member_purchases.py` — Add class docstring to `MemberPurchase`. Add field descriptions.
- `src/otf_api/models/members/notifications.py` — Add class docstrings to `SmsNotificationSettings`, `EmailNotificationSettings`.

### Studio models
- `src/otf_api/models/studios/studio_detail.py` — Add class docstrings to `StudioLocation`, `StudioDetail`. Add method docstrings to `create_empty_model`, `add_to_favorites`, `remove_from_favorites`. Add field descriptions.
- `src/otf_api/models/studios/studio_services.py` — Add class docstring to `StudioService`.
- `src/otf_api/models/studios/enums.py` — Add class docstring to `StudioStatus`.

### Workout models
- `src/otf_api/models/workouts/telemetry.py` — Add class docstrings to `Zone`, `Zones`, `TreadData`, `RowData`, `TelemetryItem`, `Telemetry`, `TelemetryHistoryItem`. Add method docstrings to `reduce_telemetry_list`.
- `src/otf_api/models/workouts/performance_summary.py` — Add class docstrings to `ZoneTimeMinutes`, `HeartRate`, `PerformanceMetric`, `BaseEquipment`, `Treadmill`, `Rower`. `PerformanceSummary` already has one — verify.
- `src/otf_api/models/workouts/lifetime_stats.py` — Add class docstrings to all 8 classes. Add method docstrings to `limit_floats`, `get_by_time`.
- `src/otf_api/models/workouts/workout.py` — `Workout` already has docstring — verify. Add `class_history_uuid` computed field docstring.
- `src/otf_api/models/workouts/body_composition_list.py` — Add class docstrings as needed.
- `src/otf_api/models/workouts/challenge_tracker_content.py` — Add class docstrings as needed.
- `src/otf_api/models/workouts/challenge_tracker_detail.py` — Add class docstrings as needed.
- `src/otf_api/models/workouts/out_of_studio_workout_history.py` — Add class docstrings as needed.
- `src/otf_api/models/workouts/enums.py` — already complete, verify only.

### Base and mixins
- `src/otf_api/models/base.py` — Add class docstring to `OtfItemBase`.
- `src/otf_api/models/mixins.py` — Add method docstrings to `set_api`, `create`, `raise_if_api_not_set`. Add method docstrings to `validate_model`, `clean_strings` on `AddressMixin`.

### Docstring format
Follow the same Google-style convention used in the API classes. Class docstrings should be brief — one or two sentences describing what the model represents. Field descriptions should be concise — what the field contains, not implementation details.

### Field description format
```python
field_name: str = Field(description="Brief description of what this field contains.")
```
For fields that already have other Field kwargs (like `exclude=True`), add `description=` to the existing Field call. Do NOT add descriptions to fields marked `exclude=True, repr=False` — these are internal and should stay undescribed.

## Focus
- This is the largest task. Work systematically through each directory rather than jumping around.
- Booking models have the most complex inheritance — `Booking` has ~27 fields, many with existing descriptions.
- Workout models at `telemetry.py` and `lifetime_stats.py` have 0% docstring coverage — start from scratch.
- Use the existing `Field(description=...)` patterns already in `classes.py` and `bookings_v2.py` as templates.
- Do NOT add descriptions to `exclude=True` fields — these should remain invisible in the docs.
- The `NOTE:` comments in `body_composition_list.py` and `challenge_tracker_content.py` contain useful context for writing docstrings.

## Verify
- [ ] FR#14: Every public class in `models/` has a class-level docstring; every public method on model classes has a method docstring
- [ ] AC#2: `python -c "from otf_api.models.workouts.telemetry import Telemetry; help(Telemetry)"` produces class and field documentation (spot check for previously undocumented models)
- [ ] AC#3: No `Field(description=...)` was added to fields with `exclude=True` — these remain undescribed for doc filtering
- [ ] AC#2: Count of documented public classes/methods across all `PUBLIC_MODULES` matches the count of entries in `__all__` exports — run a comparison script or manual spot-check across all model sub-packages
