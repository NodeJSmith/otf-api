# Design: Data Anonymization Pipeline

**Date:** 2026-04-26
**Status:** archived
**Research:** /tmp/claude-mine-define-research-Fpttnn/brief.md

## Problem

The library cannot be tested without real credentials, and users cannot share debug data without exposing personal information. Every API response contains sensitive data — names, emails, phone numbers, home addresses, birthday, credit card details, biometric measurements (weight, body composition, heart rate telemetry), financial transactions, and behavioral patterns (workout schedules, class attendance). This data appears not just in response bodies but also in request URLs, query parameters, HTTP headers, and fixture filenames.

The library currently has one test file covering 1% of the codebase — a codebase audit found three confirmed runtime bugs that would have been caught by basic tests. Every code change carries regression risk with no safety net. Users who encounter bugs must choose between sharing their private data or providing no diagnostic information, meaning bug reports lack the context needed for diagnosis and either go unresolved or require extended back-and-forth to reproduce.

## Goals

- Zero real PII values remain in anonymized output — measured by the PII validator scanning for all known real values (names, emails, phones, UUIDs, addresses, biometrics) and reporting zero matches
- 100% of anonymized fixture files parse through all existing Pydantic models without validation errors
- Referential integrity: every identifier that appears in N files maps to the same fake identifier in all N anonymized files — verified by the validator across the full fixture corpus
- Deterministic: same seed + same input produces byte-identical output across runs
- End users can produce a shareable debug archive by setting a single environment variable — no code changes, no additional dependencies to install
- The anonymization system is a documented, public API surface of the library with stable imports

## Scope Boundary

**In scope:** The anonymization pipeline itself — field mappings, anonymizer engine, generators, validator, batch mode, real-time capture mode, and the httpx hook integration.

**Out of scope:** This feature does not build a mock HTTP server for replaying fixtures, does not add a test framework or test runner configuration, does not modify existing API client behavior (the anonymizer is observational only), and does not write the actual test suite that uses the anonymized fixtures. Those are follow-up work that this feature unblocks.

## User Scenarios

### Maintainer: Library developer

- **Goal:** Generate anonymized test fixtures from real API responses
- **Context:** After capturing raw responses from the live API, before committing fixtures

#### Generate test fixtures

1. **Capture raw responses from all endpoints**
   - Sees: Script output showing which endpoints succeeded/failed
   - Then: Raw JSON files saved to a local directory (gitignored)

2. **Run the anonymizer on captured responses**
   - Sees: Progress output showing files processed, PII fields replaced
   - Decides: Whether to use default settings or configure strictness level
   - Then: Anonymized JSON files written to a separate directory, suitable for committing

3. **Validate the anonymized output**
   - Sees: Validation report confirming no real PII values remain, all models parse cleanly
   - Then: Commits anonymized fixtures to the repository

### End user: Library consumer reporting a bug

- **Goal:** Generate a sanitized debug archive to attach to a bug report
- **Context:** Encountered unexpected behavior and wants to share diagnostic data

#### Generate debug dump

1. **Enable anonymized capture**
   - Sees: Documentation explaining the configuration option
   - Decides: To set the environment variable or config flag
   - Then: Library begins capturing and anonymizing responses during normal usage

2. **Reproduce the bug**
   - Sees: Normal library behavior (anonymization is transparent)
   - Then: Anonymized responses and logs accumulate in an output directory

3. **Share the debug archive**
   - Sees: Output directory containing anonymized JSON files, a log file, and a manifest
   - Decides: To attach the directory to a GitHub issue
   - Then: Maintainer can reproduce the issue using the sanitized data

### Maintainer: Validation catches a PII leak

- **Goal:** Identify and fix a gap in the anonymizer's field mappings
- **Context:** After running the anonymizer, the validator reports leaked real values

#### Fix a mapping gap

1. **Run the validator on anonymized output**
   - Sees: Validator report listing specific files and field paths where real PII values were detected
   - Decides: Whether this is a missing mapping or an address format variance issue

2. **Update the field mappings**
   - Sees: The mappings module with the existing field classifications
   - Then: Adds the missing field path or correlation rule, re-runs the anonymizer

3. **Re-validate**
   - Sees: Validator reports zero leaks
   - Then: Proceeds to commit the anonymized fixtures

## Functional Requirements

1. The anonymizer must replace all personal identity fields (names, emails, phone numbers, birthday, gender, addresses) with realistic fake values of the same type and format
2. The anonymizer must replace all biometric fields (weight, height, heart rate, body composition measurements, age) with randomized values within realistic ranges
3. Body composition values must maintain internal consistency — related measurements must be scaled by a consistent factor per scan to preserve ratios
4. Heart rate zone boundaries must be recalculated from the anonymized max heart rate, not independently randomized
5. All identifiers (member UUID, cognito ID, person ID, MBO IDs, numeric member ID, studio UUIDs, coach UUIDs, booking UUIDs, class UUIDs) must map consistently to fake identifiers across all files in a batch
6. Auth and security tokens (access tokens, ID tokens, refresh tokens, studio tokens) must be replaced with a "REDACTED" sentinel value
7. Financial fields (credit card last 4, payment reference numbers, sale IDs, prices) must be replaced with fake values preserving format
8. Coach names, image URLs, and staff IDs must be anonymized (they are real people)
9. Studio names, addresses, phone numbers, and coordinates must be anonymized (they reveal the member's location)
10. Null values must remain null — the anonymizer must not fill in nulls with fake data
11. Fields not recognized by the anonymizer must pass through unchanged by default
12. A configurable strictness level must allow users to choose how unknown fields are handled: pass-through (default), mask with a sentinel, or drop with documentation
13. When unknown fields are masked or dropped, their existence and key names must be preserved in a manifest so bug reporters can document what fields were present
14. The anonymizer must handle all locations where personal data appears: response bodies, request URLs, query parameters, and fixture filenames
15. A post-anonymization validator must scan output for any remaining known real values and report them as failures
16. The validator must check that JSON structure is preserved (same keys, same types, same nesting, nulls preserved)
17. The validator must verify that anonymized output parses successfully through the library's existing models
18. Batch mode must process a directory of raw response files and produce a parallel directory of anonymized files
19. Real-time capture mode must hook into the HTTP client and write anonymized responses to a configurable output directory during normal library usage
20. Real-time capture mode must be activatable via an environment variable, following the existing `OTF_LOG_RAW_RESPONSE` convention
21. The replacement mapping must be deterministic given the same seed, producing identical output for the same input across runs
22. The replacement mapping must be serializable to a file alongside the anonymized output, enabling the maintainer to correlate anonymized data back to field positions (not real values) for debugging

## Edge Cases

1. **New API fields**: The upstream API adds fields the anonymizer doesn't recognize. Default behavior passes them through; strict mode flags them. The PII validator catches leaked real values regardless of mode.
2. **Biometric internal consistency**: Body composition scans contain ~50 fields with mathematical relationships (lean mass + fat mass ≈ total weight). Independent randomization produces physiologically impossible values. Must scale by a consistent factor per scan.
3. **Referential integrity across files**: A member UUID appears 89+ times across 67 files. A studio UUID appears 692+ times. The replacement map must be shared across all files in a batch.
4. **PII in filenames**: Captured fixture filenames encode URLs containing UUIDs, emails, and phone numbers. Anonymization must transform filenames too.
5. **Empty responses**: Some endpoints return empty bodies for non-GET requests. The anonymizer must handle these gracefully.
6. **Nested and varying JSON structures**: Different API hosts use different wrapper structures (`{"code": "SUCCESS", "data": {...}}` vs `{"items": [...]}` vs flat objects). The anonymizer must walk all structures recursively.
7. **URL-encoded PII**: Email addresses in query parameters are URL-encoded (e.g., `%40` for `@`). The anonymizer must handle both encoded and decoded forms.
8. **Address format variance**: The same physical address appears in different formats across endpoints (e.g., "2835 N Maize Rd., Suite 161" vs "2835 North Maize Road Suite 161"). Direct string matching in the replacement map will miss variant forms. Must use identifier-based correlation (e.g., studio UUID + address field) as a fallback to ensure all variants of the same address map to the same fake address.
9. **Concurrent API calls in real-time mode**: Multiple threads making API calls simultaneously both trigger the response hook and write to the shared replacement map. The replacement map must be thread-safe (use a lock or thread-local maps merged at session end).
10. **Disk full during batch write**: If the output directory fills up mid-batch, the anonymizer must fail with a clear error and not leave a partially-written directory that looks complete. The validator should refuse to run on incomplete output.
11. **Malformed JSON in fixture**: If a captured fixture contains invalid JSON (e.g., truncated response), the anonymizer must skip it with a warning rather than crashing the entire batch.
12. **Faker generation failure**: If Faker cannot generate a value matching the required format (unlikely but possible with custom providers), the anonymizer must fall back to a deterministic placeholder rather than passing through the real value.

## Acceptance Criteria

### Identity and contact fields (FR 1, 5, 8, 9)

Given a fixture file containing a real member name, email, phone number, birthday, gender, or address,
When the anonymizer processes the file,
Then each field is replaced with a realistic fake value of the same type and format, and the real value does not appear anywhere in the output.

Given a coach name, image URL, or staff ID in a fixture,
When the anonymizer processes the file,
Then the coach data is replaced with fake values.

Given a studio name, address, phone number, or coordinates in a fixture,
When the anonymizer processes the file,
Then the studio data is replaced with fake values.

### Referential integrity (FR 5)

Given a member UUID that appears in 30+ fixture files,
When all files are anonymized in a single batch,
Then the same fake UUID appears in every output file where the real UUID appeared.

Given an address that appears in different formats across endpoints (e.g., "2835 N Maize Rd., Suite 161" vs "2835 North Maize Road Suite 161"),
When both files are anonymized in the same batch,
Then both variants map to the same fake address — using identifier-based correlation (studio UUID + address) as a fallback when exact string matching fails.

### Biometric consistency (FR 2, 3, 4)

Given a body composition scan with ~50 related fields (weight, lean mass, fat mass, BMI, etc.),
When the anonymizer processes the scan,
Then all fields are scaled by a consistent factor so that mathematical relationships between fields are preserved (e.g., lean mass + fat mass ≈ total weight).

Given a telemetry response with heart rate data and zone boundaries,
When the anonymizer processes the response,
Then zone boundaries are recalculated from the anonymized max heart rate, and all HR values are offset by a consistent delta within the workout.

### Auth and financial (FR 6, 7)

Given a fixture containing a studioToken or auth-adjacent field,
When the anonymizer processes the file,
Then the field value is replaced with the "REDACTED" sentinel.

Given a fixture containing credit card last 4, payment reference numbers, or prices,
When the anonymizer processes the file,
Then each is replaced with a fake value preserving the original format (4 digits, integer, decimal).

### Null preservation (FR 10)

Given a fixture where a PII field (e.g., workPhone, profilePictureUrl) is null,
When the anonymizer processes the file,
Then the field remains null in the output.

### Unknown field handling (FR 11, 12, 13)

Given a fixture containing a field the anonymizer does not recognize,
When the anonymizer runs in default (permissive) mode,
Then the unknown field passes through unchanged.

Given the same fixture with an unrecognized field,
When the anonymizer runs in strict mode with mask configured,
Then the field value is replaced with a sentinel and the field name is recorded in the output manifest.

### PII in non-body locations (FR 14)

Given a fixture filename containing a member UUID, email, or phone number,
When the anonymizer processes the file,
Then the output filename has those values replaced with their fake counterparts from the replacement map.

Given a fixture with PII in URL query parameters (e.g., `email=real@example.com`),
When the anonymizer processes the associated metadata,
Then the query parameter values are replaced with fake counterparts.

### Validator (FR 15, 16, 17)

Given anonymized output from a batch run,
When the PII validator runs against it,
Then it reports zero matches for any known real PII value across all file bodies and filenames.

Given anonymized output,
When the validator checks structural integrity,
Then every output file has the same JSON keys, types, and nesting depth as the corresponding input file.

Given anonymized output,
When the validator attempts to parse each file through the corresponding Pydantic model,
Then all files parse without validation errors.

### Batch mode (FR 18)

Given a directory of raw fixture files,
When the anonymizer runs in batch mode,
Then a parallel output directory is produced with one anonymized file per input file, plus a replacement map file and validation report.

### Real-time capture mode (FR 19, 20)

Given the environment variable `OTF_ANONYMIZE_RESPONSES=true` is set,
When the library makes API calls during normal usage,
Then anonymized responses are written to the output directory transparently, without affecting the library's normal behavior.

### Determinism (FR 21)

Given the same input files and the same seed value,
When the anonymizer runs twice,
Then the output is byte-identical both times.

### Replacement map serialization (FR 22)

Given a completed batch anonymization run,
When the replacement map is written to `_anonymization_map.json`,
Then it contains entries mapping fake values to field positions (not real values) sufficient for debugging correlation.

## Dependencies and Assumptions

- **Faker library**: Used for generating realistic fake data. Added as a production dependency (not dev-only) since end-user capture mode needs it at runtime.
- **Captured fixture corpus**: The 67 raw response files serve as the test corpus for the anonymizer itself. Must be available locally (gitignored).
- **Pydantic v2 models**: The anonymizer operates on raw JSON dicts, but validation uses the existing Pydantic models. Model definitions inform the field mapping but are not directly coupled to the anonymizer.
- **httpx event hooks**: The real-time capture mode depends on httpx's event hook mechanism, which is already proven in the codebase.

## Architecture

### Package structure

New `src/otf_api/anonymize/` package:

- **`__init__.py`** — Public API: `Anonymizer`, `AnonymizeConfig`, `validate_anonymized`
- **`mappings.py`** — PII field classifications as Python dataclasses. Each mapping defines: JSON key paths, replacement strategy, and whether referential integrity is required. Uses Python code (not YAML/JSON) so field names can reference Pydantic model `validation_alias` values and replacement strategies can use callables.
- **`anonymizer.py`** — Core engine. Takes a JSON dict, walks it recursively, applies replacements from mappings. Maintains a `replacement_map: dict[str, str]` that persists across calls for referential integrity. Configurable strictness level for unknown fields.
- **`generators.py`** — Faker-backed generators for each PII category: names, emails, UUIDs, phone numbers, addresses, biometric values. Seeded for reproducibility. Body composition scaling uses a per-scan consistent factor. HR zones derived from anonymized maxHr.
- **`validator.py`** — Post-anonymization validator. Collects all known real PII values during anonymization, then scans serialized output for any matches. Also validates structural integrity and model parsing.
- **`hooks.py`** — httpx event hook for real-time capture mode. Activated by `OTF_ANONYMIZE_RESPONSES` env var. Writes anonymized JSON to a configurable output directory. Reuses the pattern from `scripts/capture_responses.py`.

### PII field taxonomy

Fields are classified into replacement strategies:

| Category | Strategy | Referential integrity | Examples |
|---|---|---|---|
| Identity (UUID) | Consistent fake UUID | Yes | memberUUId, cognitoId, person_id, studioUUId, coachUUId |
| Identity (numeric) | Consistent fake integer | Yes | memberId, mboUniqueId, studioId |
| Name | Faker name | Yes (same name → same fake) | firstName, lastName, userName, CoachName |
| Email | Faker email | Yes | email, contactEmail |
| Phone | Faker phone | Yes | phoneNumber, homePhone |
| Address | Faker address components | Per-location group | address1, city, state, postalCode |
| Birthday | Random date in plausible range | No | birthDay |
| Financial | Format-preserving fake | No | ccLast4, price, posPmtRefNo |
| Biometric (scalar) | Randomized within realistic range | No | weight, height, age, maxHr |
| Biometric (body comp) | Scale by consistent factor per scan | Per-scan group | tbw, bfm, lbm, smm, bmi, pbf, all segmental fields |
| Biometric (telemetry) | Offset all HR values by consistent delta | Per-workout | telemetry[].hr, zones.*.startBpm/endBpm |
| Auth token | "REDACTED" sentinel | No | studioToken, Authorization header |
| Timestamp | Offset by consistent random delta | Per-session | bookedDate, classStartTime, workoutDate |
| Image URL | Placeholder URL | No | imageUrl, profilePictureUrl, coach.image_url |

### Referential integrity

A `ReplacementMap` (dict-backed) persists across all files in a batch. When the anonymizer encounters a value that needs consistent replacement:

1. Check the map: if the real value is already mapped, return the existing fake
2. If not, generate a new fake value, store the mapping, return it

The map is serializable to `_anonymization_map.json` alongside output. This file maps fake values back to field positions (not real values) for debugging correlation.

### Real-time capture mode

Activated by `OTF_ANONYMIZE_RESPONSES=true` (env var) or programmatic configuration. Injects an httpx response event hook into the `OtfClient` session at initialization. The hook:

1. Reads the raw response
2. Anonymizes the JSON body using a session-scoped `Anonymizer` instance (preserving referential integrity across requests)
3. Anonymizes the request URL (replacing PII in path and query params)
4. Writes the anonymized response to the output directory
5. Returns without modifying the actual response (anonymization is observational only)

The output directory defaults to `~/.otf-api/debug/` (via `platformdirs`) and can be overridden with `OTF_ANONYMIZE_OUTPUT_DIR`.

### Seed strategy

Default: hash of the member UUID (first one encountered). This means the same user always gets the same fake data, making it easier to correlate across multiple debug dumps. Users can override with `OTF_ANONYMIZE_SEED` env var. A random seed is used if no member UUID is encountered (shouldn't happen in practice).

## Alternatives Considered

### YAML/JSON configuration for field mappings

Defining PII field mappings in a YAML or JSON config file instead of Python code. Rejected because: (a) replacement strategies require callable generators that don't serialize to config, (b) field names already exist as `validation_alias` values in Pydantic models that Python code can reference directly, (c) type checking catches mapping errors in Python but not in config files.

### Mimesis instead of Faker

Mimesis is ~12x faster than Faker. However: (a) Faker has broader provider coverage (170+ vs ~30), (b) Faker's seeded reproducibility is well-documented, (c) the performance difference is irrelevant for 67 files, (d) Faker has a much larger user base and ecosystem. Speed would only matter for real-time mode, where we're anonymizing one response at a time anyway.

### Regex-based PII detection instead of explicit field mappings

Using pattern matching (email regex, phone patterns, UUID patterns) to detect and replace PII without explicit field definitions. Rejected because: (a) false positives on non-PII fields that happen to match patterns, (b) no way to apply field-specific strategies (biometric scaling vs name replacement), (c) no way to maintain referential integrity without knowing which fields should be consistent, (d) numbers like `15704881` (memberId) don't match any useful pattern.

## Test Strategy

The anonymizer can be tested entirely without real credentials using the 67 captured fixture files as input:

1. **Unit tests for generators**: Verify each fake data generator produces values of the correct type, format, and range. Verify seeded generators produce deterministic output.
2. **Unit tests for field mappings**: Verify every known PII field from the fixture audit is covered by a mapping.
3. **Integration tests for anonymizer**: Process each fixture file through the anonymizer and verify: no known real PII values in output, JSON structure preserved, nulls preserved, referential integrity maintained across files.
4. **Validator tests**: Verify the validator catches intentionally leaked PII values and passes clean output.
5. **Model parsing tests**: Verify anonymized fixtures parse through all Pydantic models without validation errors. This also serves as the first real model-layer test coverage for the library.
6. **Filename anonymization tests**: Verify PII is removed from fixture filenames.
7. **Seed determinism tests**: Verify same seed + same input = same output across runs.

## Documentation Updates

- README: Add a section on anonymized debug dumps for bug reporting
- New docs page: Anonymization pipeline usage (batch mode for contributors, real-time mode for end users)
- Contributing guide: Document the fixture capture → anonymize → commit workflow

## Impact

**New files:**
- `src/otf_api/anonymize/__init__.py`, `mappings.py`, `anonymizer.py`, `generators.py`, `validator.py`, `hooks.py` (~6 files)
- `tests/test_anonymize/` — test files for each module (~5 files)

**Modified files:**
- `src/otf_api/api/client.py` — hook integration for real-time capture mode
- `src/otf_api/__init__.py` — export `Anonymizer` and `AnonymizeConfig`
- `pyproject.toml` — add `faker` dependency
- `scripts/capture_responses.py` — add anonymization step option

**Blast radius:** Low for existing code. The anonymizer is a new package that hooks into the existing client via a well-defined extension point (httpx event hooks). The only modification to existing code is the optional hook injection in `OtfClient.__init__`.

## Open Questions

None — all questions resolved during discovery.
