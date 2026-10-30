# Design: Open server-owned vocabularies

**Date:** 2026-10-30
**Status:** ratified
**Mode:** sketch
**Issues:** #161, #148, #158, #159
**Prior art:** design/research/2026-10-26-tolerant-response-enums/prior-art.md

## Summary

OTF can add a class type, booking status, studio status, or equipment id at any time. `ClassType`, `BookingStatus`, `StudioStatus`, and `EquipmentType` are closed enums on response models, so a new value fails validation and the list endpoints drop the whole record until a library release catches up. This milestone makes those four response fields open: an unrecognized value parses, the record is kept, the raw value is preserved, and the value is reported once.

The enums themselves stay as they are, closed and importable, and `ClassType("x")` still raises. They become the known-values view of a field that can also hold a raw value.

Homes for the new pieces:

- **Normalizing and reporting unknown values:** a small new module beside `OtfItemBase`, under `src/otf_api/models/`, because no existing class is about this. It also holds the field aliases. `None` passes through untouched for the nullable fields (`StudioStatus | None`, `EquipmentType | None`) and is neither reported nor treated as unknown.
- **What a v1 booking's state is when its status is unrecognized:** a predicate on the v1 `Booking` model in `models/bookings/bookings.py`, read from its date fields. This replaces negation written at each call site in `BookingApi`.
- **Filter comparison:** stays on `ClassFilter` in `models/bookings/filters.py`.
- **Unknown class type duration:** stays in `get_end_time` in `models/bookings/bookings_v2.py`.

The change touches, under `src/otf_api/`: `models/bookings/classes.py` (`OtfClass.class_type`), `models/bookings/bookings_v2.py` (`BookingV2Class.class_type`, `get_end_time`), `models/bookings/bookings.py` (`Booking.status`, the predicate, `__str__`), `models/bookings/filters.py`, `models/studios/studio_detail.py` (`StudioDetail.status`), `models/workouts/challenge_tracker_detail.py` and `models/workouts/challenge_tracker_content.py` (`equipment_id`), `api/bookings/booking_api.py` (`book_class`, `get_bookings`), and `api/workouts/workout_api.py` (parameter hints). Tests go in `tests/test_filters.py`, `tests/test_api/test_bookings.py`, `tests/test_api/test_workouts.py`, and `tests/test_api/test_studios.py`. Docs go in `docs/guides/bookings.md` and `docs/guides/challenges.md`, noting that consumers narrow with `isinstance` before reading `.value`, and compare by value (`==`, `in`) rather than by type, since a raw value can become an enum member in a later release.

In scope: the four vocabularies on response models, `ClassFilter` input, the booking control flow in `BookingApi`, `get_end_time`, the published OpenAPI output, and the docs for the type change.

Out of scope: `DoW`, `StatsTime`, `TrendType`, `TrendCategory`, `AverageType`, `BodyFatPercentIndicator`, and the challenge category enums, none of which validate a server response today. Replacing v1 booking calls with v2 is also out.

Done when: a response carrying an unrecognized class type, booking status, studio status, or equipment id parses with the record retained and the raw value preserved; each new value logs one WARNING per process; `book_class`, `get_bookings`, and `get_end_time` behave as D4 and D6 specify for unknown values; the output of `scripts/generate_openapi.py` shows `anyOf` an enum and an open primitive for all four; and the commit is `feat!`, with a `Closes` line for each of #148, #158, #159, and #161, and a footer naming the `.value` break on unrecognized values and the `getattr(x, "value", x)` migration idiom, which the docs repeat. The commit body also says the published schema's four fields change to `anyOf`, which some code generators collapse to a plain type.

## Posture

- **Failure handling:** keep the record and warn once per value, with no retries. A record that fails validation for any other reason is still dropped by the existing per-record handling.
- **Compatibility:** typed consumers may break under `feat!` in 0.x, with no shims. `==`, `in`, and `match` keep working at runtime for values that exactly match a member. `.value` on an unrecognized value does not, and that is the documented break.
- **Scope:** the four named vocabularies only.
- **Rollout:** ships outright through release-please, with no flag or migration. Nothing is stored.
- **Hardening:** project defaults.
- **Altitude:** `build`; at about 18 files this is one landable unit built in one session, per D8.

## Decisions

### D1: How should an open vocabulary be represented on a response model?

**Situation:** `OtfClass.class_type` is typed `ClassType`, so `"HYROX_75"` fails validation and the class disappears from `get_classes()`. The field needs to hold values the library has never seen. The prior-art brief recommended a `_missing_` pseudo-member because it changes the public types least; #161 records that this approach was tried in the abandoned #148 sketch and needed enum internals, a cache, a private constructor, and a schema hook, and still could not cover `BookingStatus` or the `IntEnum`s. It is scored here so the brief's recommendation is answered, not ignored.

**Deciding factor:** one mechanism that covers all four vocabularies, including the `IntEnum`, and tells the truth to type checkers and the published schema.

| | A: `ClassType \| str`, normalized (known value becomes the member, unknown stays raw) | B: plain `str` / `int`; enum is only named constants | C: raw `str` / `int` field plus a typed accessor property | D: `_missing_` pseudo-member (the brief's pick) |
|---|---|---|---|---|
| Known value at runtime | The enum member, so `.value` and `isinstance` work | Plain string, so `.value` fails on every value | Plain string on the field, member on the accessor | The enum member |
| Telling known from unknown | `isinstance(x, ClassType)` | Membership test against the enum | Accessor returns `None` | A custom flag on the enum |
| Type-checker honesty | Honest; consumers must narrow before `.value` | Honest, but the vocabulary disappears from the type | Honest, with two attributes per field | Dishonest; an unknown looks like a declared member |
| Published schema | `anyOf[enum, string]` with no script changes (verified) | Plain `string`; known values lost unless added by hand | Plain `string`; known values lost unless added by hand | Closed unless a schema hook is added |
| Works for `IntEnum` | Yes, as `EquipmentType \| int` (verified) | Yes | Yes | Needs a second, int-specific base |
| Machinery | One normalizer, reused per field | None for the type; reporting still needs a validator | One normalizer plus an accessor per field | Writes to enum internals, cache, constructor, schema hook |
| Existing precedent | `TrendApi.trend_type: TrendType \| str` is the same union on input | `challenge_category_id: int`, `StatPoint.class_type: str` | None | None |
| Peers | ring-doorbell (`RingEventKind \| str`), Speakeasy (`Literal \| UnrecognizedStr`) | garminconnect | unknown | No surveyed production SDK keeps the raw value this way |
| OTF's Android app | Partly: status enums are nullable, so an unknown keeps the record but loses the value | Class type is a raw `String` and equipment id a raw `Integer`, compared to literals | No | No |

**Recommendation:** A, because it is the only option where one small normalizer covers every vocabulary and the schema comes out right with no further work.
**Pick B instead if** you would rather give up the known-value members than add a normalizer, and you accept losing the vocabulary from the schema. **Pick C instead if** field types must stay plain for consumers and a second attribute per field is acceptable. **Pick D instead if** keeping `ClassType` as the field's declared type matters more than everything above.
**Reversibility:** hard (public type surface, and each later change is another `feat!`)
**Ratified:** Chose the normalized `ClassType | str` union over plain values, typed accessors, and a `_missing_` pseudo-member, to cover all four vocabularies with one mechanism and an honest type and schema, accepting that consumers must narrow before reading `.value`. "Known" means an exact match, so a near-miss spelling such as `"Late cancelled"` stays a raw value and is reported by the once-per-value WARNING.

### D2: What should `ClassFilter` do with a class type it doesn't recognize?

**Situation:** `ClassFilter(class_type="orange 60")` normalizes case and spaces, then looks the value up in `ClassType`. An unknown value raises a bare `KeyError`, which also catches typos. Once `HYROX_75` classes can be parsed, a closed filter means a caller can see those classes but cannot filter to them until a release adds the member. The opposite choice means a typo no longer fails: `"orang 60"` matches nothing.

**Deciding factor:** a class the library can return should be a class the caller can filter to.

| | A: Accept and warn; compare by normalized value on both sides | B: Keep rejecting unknown values | C: Accept silently |
|---|---|---|---|
| Filter to a brand-new type | Works, including `"hyrox 75"` matching `HYROX_75` | Impossible until a release | Works |
| Typo | No exception; empty result plus a WARNING naming the value | Fails immediately | Empty result with no signal |
| Known-value behavior | Unchanged | Unchanged | Unchanged |
| Error type on rejection | n/a | Bare `KeyError` today, and should be fixed if this stays | n/a |
| Machinery | One key function and one log line | None | One key function |
| Peers | Speakeasy's open enums accept any value; filter behavior unknown | unknown | unknown |

**Recommendation:** A, because it meets the deciding factor and leaves a visible signal for typos. The warning fires on each filter construction, not through the once-per-value reporting in D5, because a filter value is a caller's action, not a server value.
**Pick B instead if** catching typos at construction matters more than filtering on new class types the day they appear. **Pick C instead if** warnings on filter input would be noise for your callers.
**Reversibility:** easy (behavior only; tightening later is another break)
**Ratified:** Chose accepting unknown filter values with a WARNING and normalized comparison over rejecting or accepting silently, to let callers filter to any class the library can return, accepting that a typo becomes an empty result plus a log line instead of an exception.

### D3: Should API parameters that take these vocabularies widen their type hints too?

**Situation:** The `ClassFilter` input is settled separately. `BookingApi.get_bookings(status=...)` already passes a plain string through at runtime, `WorkoutApi.get_benchmarks` already coerces with `int()`, and `get_benchmarks_by_equipment` compares with `==`. Only their annotations say the closed enum. A caller holding an unrecognized value from a response gets a pyright error passing it straight back.

**Deciding factor:** the types should say what the code already accepts, so a value read from a response can be passed back in.

**Recommendation:** widen those annotations to `BookingStatus | str` and `EquipmentType | int`, with no behavior change. `get_benchmarks`'s existing `| Literal[0]` default folds into the `int`.
**Pick "leave them" instead if** you want request parameters to keep steering callers to known values, accepting a type error for a value the library itself returned.
**Reversibility:** easy
**Ratified:** Chose widening the `get_bookings` and workouts parameter hints over leaving them closed, to let a value read from a response be passed back in, accepting weaker type-checker steering toward known values.

### D4: What should an unrecognized v1 booking status mean for booking control flow?

**Situation:** `BookingV2.status` is derived from booleans and can never be unknown, so this only concerns the v1 `Booking.status` that `book_class` and `get_bookings` use. Today an unknown status drops the booking. Once it is kept, three places see it:

- **`book_class` already-booked check:** it raises `AlreadyBookedError` for any status other than `Cancelled`. A new cancel-flavored status would wrongly block rebooking.
- **`check_for_booking_conflicts`:** it treats every booking `get_bookings` returns as a conflict. The same cancel-flavored status would wrongly block a different, overlapping class.
- **`get_bookings` exclusions:** `exclude_cancelled` and `exclude_checkedin` remove one named member each.

The server is only a partial second guard. On the v1 path the client maps error 603 to `AlreadyBookedError`, so a same-class duplicate reaches it. The overlap code `BOOKING_CLASS_TIME_OVERLAP` in OTF's Android app is a string code, and the client matches string codes only on the v2 path, so nothing shows the server refuses an overlap on v1. A false local refusal has workarounds: `book_class` with a UUID string skips the overlap check, and `book_class_new` runs no local checks.

**Deciding factor:** treat an unknown status correctly from what the server actually told us, without adding much code.

| | A: Unknown never triggers a local block | B: Unknown counts as an active booking | C: Move these checks onto v2 bookings | D: For an unknown status, derive the state from `cancelled_date` and `checked_in_date` |
|---|---|---|---|---|
| Cancel-flavored unknown | Booking proceeds, but it shows as live in `get_bookings` | False `AlreadyBookedError` or conflict; bypass with `book_class_new` | Handled by booleans | Proceeds and is removed by `exclude_cancelled`, if the date is set |
| Active-flavored unknown | Same-class refused by the server (603); an overlap relies on an unverified server check | Blocked locally | Handled by booleans | Blocked locally |
| Known statuses | Every member behaves exactly as today | Exactly as today | Change in shape; v1 and v2 IDs differ and listings converge slowly | Every member behaves exactly as today; dates are read only for an unknown status |
| Evidence available | Client's 603 mapping | Today's code | Documented v1/v2 gotchas count against it; live data shows the two lists agree | 49 of 49 live v1 records fit the rule (see Assumed); a future status could differ |
| Size | One predicate and two call sites | Smallest | Rewrite; a separate project | One predicate on two date fields, used by `book_class` and the two exclusions |
| Peers | unknown | unknown | unknown | unknown |
| OTF's Android app | Booking refusals come from server error codes; whether it also pre-checks locally wasn't traced | Its "upcoming" list is defined by exclusion, so an unknown (null) status shows as upcoming, but that is display, not booking | Its newer bookings model does carry booleans | Not used for this in the code read |

In every option an unknown status stays a retained record, because the posture keeps it. Under D, a set `cancelled_date` means cancelled, a set `checked_in_date` means checked in, and neither means active; if both are set, cancelled wins, so `book_class` permits rebooking. The `Booking` predicate returns one of cancelled, checked in, or active for every status. Known members map as they behave today: `Cancelled` is cancelled, `CheckedIn` is checked in, and every other member is active, and dates are read only for an unknown status. `exclude_cancelled` and `exclude_checkedin` apply that state and otherwise state what they remove as positive membership, and `book_class` refuses unless the state is cancelled. `check_for_booking_conflicts` needs no change, because it only sees what those exclusions leave. This also leaves one existing oddity alone: `LateCancelled` still blocks rebooking and is still not excluded by `exclude_cancelled`. That is unrelated to unknown values and would be a behavior change to a known status.

**Recommendation:** D, because the record itself usually says what an unknown status means, so the guards and the list agree, and its failure case has a workaround.
**Pick A instead if** a false refusal is worse for you than an unverified overlap. **Pick B instead if** sending a booking request on an unknown status worries you more than wrongly refusing one. **Pick C instead if** you are retiring the v1 booking path as part of this change.
**Reversibility:** easy (one predicate)
**Ratified:** Chose deriving an unknown status's state from `cancelled_date` and `checked_in_date` over never blocking locally, counting it as active, or moving to v2, so the guards and the list act on what the server recorded, accepting that a new cancel-flavored status that sets no date is wrongly refused until a release, with `book_class_new` as the workaround.

### D5: How should unrecognized values be reported?

**Situation:** the #147 incident logged about 70 multi-line warnings per `get_classes` call against one studio, because a hautomate poll hit the same two values repeatedly. Once values are kept there is no validation error to log at all, so without new reporting a new vocabulary value would be invisible.

**Deciding factor:** the maintainer finds out a value is new without the consumer's log being flooded.

| | A: WARNING once per (vocabulary, value) per process, from the normalizer | B: WARNING on every occurrence | C: DEBUG only | D: A public registry of seen values, no logging |
|---|---|---|---|---|
| New value noticed | Yes, in a default log | Yes | No, unless debugging | Only if a consumer looks |
| Log volume on list endpoints | One line per new value | The #147 flood again | None | None |
| State | One module-level set, which needs a reset for tests | None | None | Module-level set plus public API |
| Thread safety | A race can log a duplicate line; harmless | n/a | n/a | n/a |
| Peers | None of the surveyed projects dedupe | stravalib | unknown | None |

**Recommendation:** A, because it is the only option that surfaces the value without flooding. The line names the vocabulary and the value, not the record. `get_end_time`'s warning for an unrecognized type moves down to DEBUG, since the value has already been reported at parse time and `ends_at` is read repeatedly.
**Pick B instead if** you would rather keep the code stateless and rely on log aggregation to dedupe. **Pick C instead if** consumers should never see a library warning for a server's addition. **Pick D instead if** consumers should decide for themselves what to do about new values.
**Reversibility:** easy
**Ratified:** Chose one WARNING per vocabulary and value per process, emitted by the normalizer, over warning every time, DEBUG only, or a public registry, to surface new values without flooding logs, accepting one module-level set and a rare harmless duplicate line, that the set can grow without bound on a pathological payload until a restart, and that it logs server values unescaped as the library does today.

### D6: What duration should `get_end_time` use for an unrecognized class type?

**Situation:** `get_end_time` matches on `ClassType` and already falls through to start time plus 60 minutes. A raw string falls into the same arm (verified). Only `BookingV2Class.ends_at` uses it, because v1 classes and `OtfClass` get their end time from the server, so booking conflict checks are unaffected. Class type names often carry their length (`ORANGE_90`, `TREAD_50`), though `OPEN_STUDIO` does not.

**Deciding factor:** keep `ends_at` a `datetime`, and give new formats their likely length when the name states one.

| | A: Keep the 60-minute fallback | B: Parse a trailing number in range (match `_(\d+)$`, accept 30 to 120 inclusive), otherwise 60 | C: Return `None` or raise | D: Match the app's 45-minute fallback |
|---|---|---|---|---|
| `HYROX_75` | 15 minutes short | Correct | No end time | 30 minutes short |
| Non-duration suffix, e.g. `CLASS_2`, `OPEN_STUDIO_24`, `TREAD_50_V2` | 60 minutes | 60 minutes | No end time | 45 minutes |
| `BookingV2.ends_at` type | `datetime` | `datetime` | `datetime \| None`, or an exception on a read, and it no longer matches v1's `ends_at` | `datetime` |
| New logic | None | One regex and one range check | Type change on the v2 models | None, but changes today's result for `OTHER` too if kept consistent |
| Peers | unknown | unknown | unknown | unknown |
| OTF's Android app | No | No | No | Yes: `OTHER` and every unrecognized type get 45, which also means `HYROX_60` gets 45 there |

**Recommendation:** B, because a format like `HYROX_75` states its own length, and the range keeps a non-duration suffix at the existing 60-minute fallback. The app's 45 isn't worth copying, since it gives a known 60-minute format the wrong length.
**Pick A instead if** a correct end time for a new format isn't worth a regex and a range for one property. **Pick C instead if** a wrong end time is worse than no end time for your consumers. **Pick D instead if** matching what members see in the app matters more than the likely length.
**Reversibility:** easy
**Ratified:** Chose parsing a trailing number from an unrecognized class type with a 60-minute fallback over a flat 60, no end time, or the app's 45, to give formats like `HYROX_75` their likely length, accepting that this is best effort with no guarantee. The rule is: match `_(\d+)$`, accept 30 to 120 inclusive, otherwise 60; known types and `OTHER` are unchanged.

### D7: Should the open-field machinery be public API?

**Situation:** each field needs the union plus the normalizer. A consumer writing their own type hints or narrowing can already use `ClassType | str` and `isinstance(x, ClassType)` without importing anything new.

**Deciding factor:** every public name in a semver'd library is one more thing to keep stable.

**Recommendation:** keep the normalizer and field aliases internal to the models layer, adding nothing to `otf_api.models.__all__`. Document the `isinstance` pattern instead.
**Pick "export them" instead if** you expect consumers to subclass these models and want the same behavior on their own fields.
**Reversibility:** easy (exporting later is additive)
**Ratified:** Chose keeping the normalizer and field aliases internal to the models layer over exporting them, to add no new semver-bound names, accepting that a consumer subclass adding its own open field writes its own validator.

### D8: How should this land?

**Situation:** the change touches models, filters, booking logic, workouts, and the schema. #161 asks for independently landable units. A suggested order was by layer: control flow first, then field types, filters, and schema. But `ClassType` is what has actually caused an outage, and `BookingStatus` carries the only real behavioral risk.

**Deciding factor:** the least process for a change this size, while keeping the risky part recoverable. The whole change is about 18 files and roughly 150–250 source lines (estimated from the scan), with about 7 field annotations changing and one behavior change that carries risk.

| | A: One PR, `build` altitude | B: Two PRs: everything else, then `BookingStatus` | C: Foundation with `StudioStatus`, then one issue per remaining vocabulary | D: One issue per layer |
|---|---|---|---|---|
| Review size | About 18 files in one pass | About 14 files, then about 6 | 3–8 files each | "Field types" is nearly the whole change |
| Process | One build session | Two issues, two pickup sketches | Four issues, four pickup sketches | Several issues and pickup sketches |
| Reverting the booking behavior | Reverts everything, or fix forward | Revert that PR alone | Revert that PR alone | Revert that PR alone |
| `ClassType` fix waits on booking review | Yes, but it is one review | No | No | Yes; control flow goes first |
| Half-open intermediate state | None | Briefly | Longest | Control flow ships with no open values to exercise it |
| Breaking releases | One | One or two | Up to four, or one if the release PR waits | Up to four, or one if the release PR waits |
| Closes | #148, #158, #159, #161 together | #148 and #159, then #158 and #161 | One per issue; the last closes #161 | One per issue; the last closes #161 |
| Peers | unknown | unknown | unknown | unknown |

**Recommendation:** A, because splitting only buys separate revert of the booking predicate, which is a weak reason: D4's ratified sentence names its one failure case, and the fix for that would be a small change to one predicate.
**Pick B instead if** you want the booking change to be separately revertible and that is worth two more sketch rounds. **Pick C instead if** you expect to pick these up at different times, well apart. **Pick D instead if** you want the control-flow change to prove itself in a release before any field opens.
**Reversibility:** easy until the build starts
**Ratified:** Chose one PR built from this ledger at `build` altitude over two PRs, per-vocabulary issues, or per-layer issues, to minimize process for a change of about 18 files, accepting that reverting the booking behavior alone means fixing forward.

## Assumed

- A plain `C | str` union without normalization always yields `str` for a plain string input, including known values. Evidence: probe on pydantic 2.7.3 (the project's lower bound) and the prior-art brief.
- A normalized union yields the member for known values and the raw value for unknown ones, from both Python and JSON input, and dumps to the raw value. Evidence: same probe.
- `StrEnum` and `IntEnum` members compare equal to their raw values, so `==`, `in`, and `match` value patterns work on either form. Evidence: same probe.
- Only `EquipmentType` among the `IntEnum`s validates a response; challenge category and sub-category fields are already plain `int`. Evidence: the challenge tracker models, and #159's investigation.
- `BookingV2.status` is derived from booleans and stays a `BookingStatus`, so `BookingStatus.priority()` keeps working in v2 deduplication; it has no other caller. Evidence: `BookingV2`.
- Inside the library, `.value` is read on these fields only in `Booking.__str__`, `BookingV2.__str__`, and a `get_bookings` branch already guarded by `isinstance`. `Booking.__str__` must stop assuming a member. Evidence: repo search.
- The first-party `personal-apis` adapter reads these fields through `getattr(value, "value", value)`, so it tolerates raw values. Evidence: `personal_apis.otf.models`.
- On the v1 path the server's same-class duplicate error reaches `AlreadyBookedError`. Evidence: `OtfClient._map_http_error`. Whether v1 refuses a time overlap is unverified.
- v1 date fields track status on real data: of 49 records, `Cancelled` (23) and `Late Cancelled` (2) all have `cancelledDate` and no `checkedInDate`, `Checked In` (13) all have `checkedInDate` and no `cancelledDate`, and `Booked` (11) have neither. Evidence: a read-only capture of one account on 2026-10-30.
- v1 and v2 list the same classes: over the 30 class times since 2026-09-15, none appeared on only one endpoint, and status and MBO ID agreed on all 11 where each side had one row. v1 returned nothing earlier than that date, while v2 reached back to June. Evidence: same capture.
- `ClassType` already includes `HYROX_60` and `OPEN_STUDIO`, and #147 is closed. Evidence: `ClassType`, issue state.
- OTF's own Android app does not treat these vocabularies as closed. Class type and equipment id are raw values, the two status vocabularies are nullable Gson enums, which read an unknown as null by Gson's default rather than failing, and neither `HYROX` nor `OPEN_STUDIO` appears in the app source. Evidence: `android_revenge` decompilation of app 5.4.0 and smali of a newer build (27277377), including the bytecode of `BookedClass.durationFromClassType`, because the decompiled Java of that method is marked incorrect. This shows how the client is written, not what the server currently sends.
- The OpenAPI script is run in CI and at release, and uses `model_json_schema` with no enum special-casing. Evidence: the test and release workflows, and the script.

## Build

- [x] Implementation and tests committed
- [x] Docs
- [ ] Ship-time challenge

**Calls made during the build:**

- Field aliases live beside their enums in each package's `enums.py`, not in `models/vocabulary.py`: the module importing all three enum modules is a real import cycle (`workouts` → `bookings` package init, which is still partial). The normalizer and reporting stay in `vocabulary.py`, and nothing is added to `__all__`, so D7 holds.
- The normalizer is an `AfterValidator` on the union rather than a before-validator: it needs no `None` handling because the `| None` sits outside the alias, the reported value is always hashable, and a value of the wrong type fails the record without first being reported as new.
- `get_bookings` keeps list support and is typed `BookingStatus | str | list[BookingStatus] | list[str] | None`; `ClassFilter.class_type` likewise uses `list[ClassType] | list[str]`. `list` is invariant, so `list[BookingStatus | str]` would reject an existing `list[BookingStatus]`, including `HISTORICAL_BOOKING_STATUSES` and `ClassType.get_standard_class_types()`.
- `Booking.state` returns a `Literal`, with no new enum, so nothing new needs exporting or keeping stable beyond one property.
- `class_type_key` lives in `bookings/enums.py` and `ClassType.get_case_insensitive` now calls it, so one function owns how class type names are folded. The method's behavior is unchanged.
- `filter_classes` wraps a non-list `class_type`, because the existing code supports attributes set after construction, which skip the validator. Iterating a bare string would otherwise compare characters.
- The once-per-value and per-construction warnings are pinned by patching the logger and counting calls, not by asserting message text, because the log line is itself the behavior D2 and D5 specify.
- `get_end_time`'s `OTHER` warning stays at WARNING: D5 moves only the unrecognized-type arm to DEBUG, and D6 leaves `OTHER` unchanged.
- `docs/guides/studios.md` also gets the narrowing note, which the Summary's doc list omits, because `StudioDetail.status` is one of the four open fields and that guide prints it.
