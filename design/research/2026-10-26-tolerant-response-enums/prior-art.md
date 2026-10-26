---
topic: "Tolerating unknown server-added string enum values in typed Python API clients"
date: 2026-10-26
status: Draft
---

# Prior Art: Tolerating Unknown Response Enum Values

## The Problem

OTF adds string enum values server-side without an app release. otf-api validates response fields against closed `StrEnum`s, so a new value (`HYROX_60`, `OPEN_STUDIO` in #147) fails Pydantic validation and the whole record is dropped until a library release catches up. #148 proposes tolerating unknowns: keep the raw string, and warn once per distinct value.

The question is which representation to use for an unknown value: a `_missing_` pseudo-member, an UNKNOWN/OTHER sentinel, or `Enum | str` field typing. Each one affects downstream filters, `match` statements (e.g. `get_end_time`), and type-checker exhaustiveness differently.

## How We Do It Today

- Response-facing enums are closed `StrEnum`s: `ClassType` (on `OtfClass` and `BookingV2`), `BookingStatus` and `StudioStatus`.
- Unknown values raise during validation. List endpoints catch the error per record, log a WARNING containing the full raw dict, and drop the record. See `booking_api.py:128-135`, `:266-275` and `:602`, and `studio_api.py:46-50`.
- `BookingV2.get_end_time` matches on `ClassType`, with a `case _` WARNING branch.
- `StudioStatus` already has a real member named `UNKNOWN = "Unknown"`.
- There is no `_missing_` hook anywhere in `src/`.

## Patterns Found

### Pattern 1: `_missing_` pseudo-member (raw value preserved, enum-typed)

**Used by**: Pydantic maintainer guidance (discussion #2468), in its default-member form. The Kos/open-enum and fbenum third-party libraries. No surveyed production SDK uses the variant that keeps the raw value.

**How it works**: `_missing_` runs when `Cls(value)` fails, and Pydantic v2 enum validation goes through the same lookup. Returning `str.__new__(cls, value)` with `_name_`/`_value_` set produces an instance of the enum that carries the raw string. Tested locally on Python 3.12.3 and pydantic 2.7.3:
- Model validation and JSON dump work, and dump emits the raw string. Pickle and deepcopy round-trip.
- `x == ClassType.ORANGE_60` is False, so filters behave correctly.
- `match` falls through to `case _`.
- Identity holds only if the pseudo-member is cached in `_value2member_map_`.

**Strengths**: Field types stay `ClassType`. Existing `==`, `match` and filter code keeps working unchanged, and the raw value round-trips.

**Weaknesses**:
- Relies on semi-internal enum attributes.
- Type checkers treat the value as a known member, so `assert_never` exhaustiveness gives false assurance.
- `x in C` behavior differs across Python versions (3.12 changed `__contains__`).
- Caching mutates the class registry process-wide.
- Warn-once needs module-level state.

**Example**: https://github.com/pydantic/pydantic/discussions/2468, https://github.com/Kos/open-enum

### Pattern 2: UNKNOWN / OTHER sentinel member

**Used by**: stravalib (lossy, maps to `"Workout"` and warns on every occurrence), Oracle OCI SDK (`UNKNOWN_ENUM_VALUE`, lossy), Fern Python (opt-in `_UNKNOWN` that keeps the raw value), Stainless Java (`_UNKNOWN` plus `_value()`), Apollo (`__Unknown(raw)`), serde `#[serde(other)]` (lossy).

**How it works**: One extra member receives every unrecognized value. The lossy form discards the raw string. The lossless form pairs the sentinel with the raw string, through a wrapper type or a sibling accessor.

**Strengths**: Exhaustiveness is honest, because `match` must handle `UNKNOWN`. This is closest to protobuf open-enum semantics.

**Weaknesses**:
- The lossy form collapses distinct unknowns, so HYROX_60 and OPEN_STUDIO become indistinguishable. Picking a real-looking fallback, as stravalib does with `"Workout"`, misclassifies silently.
- The lossless form needs a side channel for the raw value.

**Example**: https://github.com/stravalib/stravalib/blob/main/src/stravalib/model.py, https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/forward-compatibility.html, https://www.stainless.com/blog/making-java-enums-forwards-compatible

### Pattern 3: `Enum | str` / `Literal[...] | str` field typing

**Used by**: Speakeasy Python, with `Union[Literal[...], UnrecognizedStr]` on by default. ring-doorbell's `RingEventKind | str`. openai-python uses `Literal` but builds responses without validation, so unknowns pass through as untyped strs and its types claim a closed set.

**How it works**: Pydantic smart-union returns the enum member on an exact match and the raw str otherwise. Unknowns are detected with `x not in Enum`.

**Strengths**: No custom enum machinery. The raw value is preserved. This is the best-established approach in generators.

**Weaknesses**:
- Every consumer sees a union.
- Because `str` absorbs everything, checkers cannot enforce handling of the unknown case.
- `match` against the enum needs a `case str()` arm.

**Example**: https://www.speakeasy.com/docs/manage/forward-compatibility

### Pattern 4: Don't enumerate response values

**Used by**: python-garminconnect (dicts, plus a typed layer with `str` fields and `extra="allow"`) and ring-doorbell (response kinds kept as strings).

**How it works**: Enums are used only for request-side values, and server-sourced values stay plain strings.

**Strengths**: Nothing can fail validation.

**Weaknesses**: Gives up typing on response fields, which is the point of otf-api's model layer.

**Example**: https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/typed.py

### Pattern 5: Accept the breakage / document "open enums"

**Used by**: openapi-python-client (strict enums, no "allow unknown" option found) and stravalib's underlying generated types. Stripe documents open versus closed enums and tells consumers to code a default branch.

**How it works**: Ship a release when the server adds a value, and document the limitation.

**Strengths**: Zero machinery.

**Weaknesses**: Records are dropped until consumers upgrade. That is the #147 failure itself.

**Example**: https://docs.stripe.com/api/enums

## Anti-Patterns

- **Lossy, real-looking fallbacks.** stravalib maps unknown types to `"Workout"`, which misclassifies silently. #147's proposed "map to `OTHER`" is the same mistake, because `OTHER` is a real OTF class type.
- **Warning on every occurrence.** stravalib warns per validation, which floods logs on list endpoints. None of the surveyed projects dedupe the warning.
- **Types that lie.** openai-python annotates `Literal[...]` but returns unvalidated strs, so static exhaustiveness passes while runtime fails open.

## Emerging Trends

Generators are converging on open enums that keep the raw value: Speakeasy has it on by default for Python, Fern ships it as opt-in, and Stainless does it for Java. Protobuf proto3 and Apollo settled on the same design years ago. The shape that keeps type-checker help is "known members plus a separately typed unknown carrying the raw value" (`UnrecognizedStr`, `__Unknown(raw)`, `_UNKNOWN` plus `_value()`).

## Relevance to Us

- #147's own fallback (unknown → `OTHER`) is the stravalib anti-pattern. It loses HYROX_60 versus OPEN_STUDIO and makes `OTHER` filters match classes that aren't OTHER. #148 supersedes it.
- Every option that keeps the raw value is used by someone. The real trade-off is between consumer ergonomics and type-checker honesty:
  - The pseudo-member keeps `ClassType` as the field type, and existing filters and `match` work unchanged. But pyright believes it is a declared member.
  - `ClassType | str` is what Speakeasy does and what is easiest to defend. It is a visible type change for consumers of a public, semver'd library, though, and every `.class_type` access becomes a union.
- Warn-once deduplication isn't done by any project in the survey. It is cheap (a module-level set), and it fixes the flooding problem stravalib has.
- `get_end_time` must treat unknowns explicitly under any option, because both the pseudo-member and the str fall to `case _`.

## Recommendation

Use a tolerant `StrEnum` base whose `_missing_` returns a cached pseudo-member carrying the raw value, with a once-per-(enum, value) WARNING. This changes the public type surface least. It leaves filters and `match` correct, keeps the raw value for display and round-trip, and is the mechanism Pydantic's maintainers endorse. The `Enum | str` union is the established alternative if honest typing matters more than API stability. Weigh the two in the sketch.

Take these regardless of which option is chosen:
- Add `HYROX_60` and `OPEN_STUDIO` as real members.
- Drop #147's "map to OTHER" fallback.
- Remove the full-dict log dumps.

Coverage gap: none of the peer projects use the pseudo-member variant that keeps the raw value in production, so its long-term pitfalls (behavior across Python versions, pickling between processes) are only covered by our local test on Python 3.12, not by field experience. CI also runs 3.11, which needs checking.

## Sources

These URLs were not live-verified.

### Reference implementations
- https://github.com/stravalib/stravalib/blob/main/src/stravalib/model.py: `RelaxedActivityType`, lossy fallback with a warning on every occurrence
- https://github.com/python-ring-doorbell/python-ring-doorbell/blob/main/ring_doorbell/const.py: response kinds kept as raw strings
- https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/typed.py: `str` fields, `extra="allow"`
- https://github.com/openai/openai-python: `Literal` types with unvalidated `construct()`
- https://github.com/Kos/open-enum: `OpenEnum` with `UNKNOWN` marker
- https://github.com/vadim-su/fbenum: Pydantic adapter with MISSING member

### Blog posts & writeups
- https://www.speakeasy.com/blog/open-enums
- https://www.stainless.com/blog/making-java-enums-forwards-compatible

### Documentation & standards
- https://www.speakeasy.com/docs/sdks/customize/data-model/enums
- https://www.speakeasy.com/docs/manage/forward-compatibility
- https://buildwithfern.com/learn/sdks/features/forward-compatibility
- https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/forward-compatibility.html
- https://docs.stripe.com/api/enums
- https://protobuf.dev/programming-guides/enum/
- https://serde.rs/variant-attrs.html
- https://github.com/pydantic/pydantic/discussions/2468
- https://github.com/OAI/OpenAPI-Specification/issues/1552
