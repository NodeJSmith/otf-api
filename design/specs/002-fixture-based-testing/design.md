# Design: Fixture-Based Test Suite

**Date:** 2026-04-26
**Status:** archived

## Problem

The library's test suite requires real OrangeTheory Fitness credentials to run. This means CI pipelines cannot execute tests without storing production credentials in secrets, contributors cannot run tests without active memberships, and there is no regression safety net when API response shapes change. The existing test coverage is minimal — only model filter tests and anonymizer tests exist.

## Goals

- Every public read-only API method has at least one automated test that verifies Pydantic model parsing against realistic response data
- Tests run without network access or credentials — fully offline, fully reproducible
- CI pipelines can run the full test suite on every PR
- Schema drift (upstream API changes) is caught before release

## Non-Goals

- Testing write/mutation endpoints (book, cancel, update) — separate PR
- Testing the anonymization pipeline — already has its own test suite
- End-to-end integration tests against the live API
- Performance or load testing

## User Scenarios

### Developer: Library maintainer
- **Goal:** Run tests locally and in CI without credentials
- **Context:** After making code changes, before committing

#### Run the test suite
1. **Execute tests**
   - Sees: All tests pass or fail with clear error messages
   - Then: Confident that Pydantic models parse correctly against real response shapes

#### Add a test for a new endpoint
1. **Capture a new fixture**
   - Sees: Instructions for running the capture and anonymize scripts
   - Decides: Which endpoint to capture
   - Then: New anonymized fixture added to the fixtures directory

2. **Write the test**
   - Sees: Existing test patterns to follow
   - Then: New test loads the fixture and asserts model parsing

### Contributor: External developer
- **Goal:** Verify changes don't break model parsing
- **Context:** Submitting a PR without OTF credentials

#### Run tests without credentials
1. **Clone and test**
   - Sees: Tests pass using bundled fixtures — no credential setup needed
   - Then: Confident their changes are safe to submit

## Functional Requirements

1. A fixture loading utility shall read anonymized response files by semantic name and return the parsed response body
2. An HTTP mock transport shall intercept outgoing requests and return the matching fixture response based on URL path pattern
3. A test client factory shall produce a fully functional API client with authentication bypassed and caching disabled
4. Each public read-only method in the bookings, members, studios, and workouts APIs shall have at least one test that:
   a. Calls the method through the mock transport
   b. Asserts the return value is the correct Pydantic model type
   c. Asserts at least one key field has the expected type (e.g., UUIDs are strings, dates parse, enums resolve)
5. Tests shall not require network access, environment variables, or external state
6. The fixture index shall map semantic filenames to their original URL patterns for route matching

## Edge Cases

1. Fixture file contains an empty list response — model parsing should return an empty collection, not fail
2. Fixture file contains fields unknown to the Pydantic model — should be silently ignored (models use `extra="ignore"`)
3. Multiple fixtures exist for the same URL path with different query parameters — route matching must differentiate by params
4. API methods that trigger multiple internal HTTP requests (e.g., `get_workouts` paginating across performance summaries) — mock must serve all required sub-requests

## Acceptance Criteria

Given no `OTF_EMAIL` or `OTF_PASSWORD` environment variables are set,
When a developer runs `uv run pytest`,
Then all tests pass with zero failures and no network connections are attempted.

Given a test calls a read-only API method (e.g., `otf.members.get_member_detail()`),
When the mock transport receives the outgoing HTTP request,
Then it matches the request URL to the correct fixture via `index.json` and returns the fixture's JSON body as the response.

Given the mock client factory is invoked,
When an `Otf` instance is created,
Then authentication is bypassed (no Cognito calls), caching uses a temporary directory, and the client is fully functional against the mock transport.

Given a developer adds a new fixture file to `fixtures/anonymized/` and updates `index.json`,
When they write a test function that calls the corresponding API method,
Then no additional setup, configuration, or boilerplate is required beyond importing the mock client fixture.

Given the full test suite runs,
When execution completes,
Then at least one test exists for every public read-only method across bookings, members, studios, and workouts namespaces, and total runtime is under 10 seconds.

Given the fixture index maps a semantic filename to a host, path, and query parameters,
When the mock transport registers routes at startup,
Then each index entry produces a respx route that matches requests to the correct fixture, including disambiguation by query parameters for endpoints with multiple fixtures.

## Dependencies and Assumptions

- **respx** library for httpx request mocking (needs to be added as a dev dependency)
- Anonymized fixtures in `fixtures/anonymized/` are committed to the repository
- The `index.json` mapping file is maintained alongside fixtures
- Existing `OtfItemBase(extra="ignore")` setting means unknown fields won't cause parse failures

## Architecture

### Fixture Loading

A `load_fixture(name)` helper in `tests/conftest.py` reads from `fixtures/anonymized/{name}.json` and returns the parsed JSON. The `index.json` file maps each fixture to its original host, URL path, and query parameters.

### Mock Transport

Use **respx** (httpx mocking library, similar to responses for requests) to intercept HTTP requests. A `mock_otf` pytest fixture in `tests/test_api/conftest.py` will:

1. Create a mock `OtfUser` with fake `member_uuid`, `cognito_id`, `email_address`, and `httpx_auth=None` (httpx accepts `None` — pattern already used in `tests/test_anonymize/test_client_integration.py`)
2. Patch `OtfUser.__init__` to return the mock user (bypasses Cognito entirely)
3. Register respx routes from `index.json` — each entry maps a URL pattern to a fixture file
4. Disable diskcache by patching `get_cache()` to return a temporary cache directory
5. Return an `Otf` client instance wired to the mocked transport

### Route Matching Strategy

The `index.json` provides `host`, `path`, and `params` for each fixture. Routes are registered with respx using URL pattern matching:

- Exact path matches for simple endpoints (e.g., `/member/members/{uuid}/memberships`)
- Path prefix + param matching for parameterized endpoints (e.g., `/challenges/v3/member/{uuid}/benchmarks` with `equipmentId=2`)
- Multiple fixtures for the same path are differentiated by query parameters

UUIDs in paths are replaced with the mock user's `member_uuid` at registration time.

### Test Organization

```
tests/
  conftest.py              # load_fixture(), mock_otf_client fixture
  test_api/
    conftest.py            # shared fixtures for API tests
    test_bookings.py       # bookings API read-only tests
    test_members.py        # members API tests
    test_studios.py        # studios API tests
    test_workouts.py       # workouts API tests (largest — benchmarks, telemetry, etc.)
```

### Key Files Modified

- `pyproject.toml` — add `respx` to dev dependencies
- `tests/conftest.py` — new: fixture loading + mock client factory
- `tests/test_api/` — new: test modules for all 4 API namespaces

### What Gets Bypassed

| Component | Strategy |
|-----------|----------|
| AWS Cognito auth | Mock `OtfUser` with `httpx_auth=None` |
| HTTP requests | respx intercepts, returns fixture data |
| diskcache | Patched to use temp directory (or `FanoutCache(None)`) |
| `atexit` session cleanup | No-op (mock session) |

## Alternatives Considered

### VCR.py / vcrpy
Record-and-replay library that intercepts at the socket level. Rejected because: records raw HTTP including auth headers (credential leak risk), harder to anonymize after the fact, and the anonymization pipeline already produces clean fixtures. respx is purpose-built for httpx and gives more control over route matching.

### pytest-httpx
Another httpx mocking library. Viable, but respx is more widely used and has better documentation for complex route matching patterns (wildcard paths, param matching).

### Custom httpx Transport
Write a custom `httpx.BaseTransport` that reads from fixture files. More control but significantly more code to maintain. respx provides this abstraction out of the box.

## Test Strategy

This feature *is* the test strategy. The mock transport and fixture infrastructure enable testing the full Pydantic parsing pipeline for all API endpoints. Coverage target: every public read-only method in all 4 API namespaces.

Test quality verification: after implementation, run a quick mutation check — temporarily break a model field type and confirm a test catches it.

## Impact

- **New files:** `tests/conftest.py`, `tests/test_api/conftest.py`, 4 test modules
- **Modified files:** `pyproject.toml` (add respx dependency)
- **Committed fixtures:** `fixtures/anonymized/` (66 JSON files + index.json) — ~2MB total
- **CI:** Tests will run on every PR without credential setup
- **No breaking changes** to existing code — purely additive
