# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- PII anonymization pipeline (`otf_api.anonymize`) with 17 field categories, Faker-backed generators, and seeded determinism
- Core anonymizer engine with recursive JSON walker, referential integrity via `ReplacementMap`, and configurable strictness modes (permissive/mask/drop)
- Domain-specific transforms: body composition scaling (preserving mathematical relationships), HR telemetry offsetting with zone recalculation, address format correlation by studio UUID
- PII validator with case-insensitive leak detection, structural integrity checks, and Pydantic model parsing
- Batch anonymization script (`scripts/anonymize_fixtures.py`) and `anonymize_batch()` API for processing fixture corpora
- Real-time capture mode via `OTF_ANONYMIZE_RESPONSES=true` env var — automatically anonymizes all API responses to a debug output directory
- Response capture script (`scripts/capture_responses.py`) for recording raw API responses to disk
- 86 tests across 7 test modules for the anonymization pipeline

### Fixed

- `OutOfStudioWorkoutHistory` zone seconds fields changed from `int | None` to `float | None` to match API drift
