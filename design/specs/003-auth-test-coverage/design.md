# Design: Auth Module Test Coverage

**Date:** 2026-04-27
**Status:** approved

## Problem

The authentication module has zero automated test coverage across 617 lines of code. This means token lifecycle bugs (refresh failures, expired token handling), device key corruption, credential resolution errors, and cache interaction defects go undetected until they surface in production. A recent codebase audit already caught an infinite recursion bug in the cache module that would have been caught by even basic tests. Additionally, a latent bug exists in the credential prompting logic — a bare `raise` statement with no active exception context will crash with `RuntimeError` instead of producing a meaningful error when credentials are unavailable in non-interactive environments.

## Goals

- Achieve 80%+ line coverage on each auth module file (auth.py, user.py, utils.py) and the cache module (cache.py)
- All tests run without real OrangeTheory credentials or network access
- At least one dedicated test covers each of: token refresh, token expiry handling, device setup, credential resolution from env vars, credential prompting, standard request signing, and SigV4 request signing
- The bare `raise` on utils.py:31 is replaced with an explicit `NoCredentialsError` and a regression test verifies the fix

## Non-Goals

- No structural refactoring of the authentication class (testable as-is by mocking at boundaries)
- No integration tests against real authentication services
- No changes to the existing API test suite

## User Scenarios

### Developer: Library Maintainer
- **Goal:** Verify auth behavior without real credentials
- **Context:** Running the test suite locally or in CI after code changes

#### Run auth tests offline
1. **Execute test suite**
   - Sees: All auth tests pass, coverage report shows 80%+ per file
   - Decides: Whether the change is safe to merge
   - Then: CI confirms the same results

#### Catch a token refresh regression
1. **Modify token refresh logic**
   - Sees: Specific test failure pointing to the broken behavior
   - Decides: How to fix the regression
   - Then: Fix is verified by the same test passing

### Developer: New Contributor
- **Goal:** Understand auth behavior through tests
- **Context:** Reading test files to learn how authentication works

#### Learn auth flow from tests
1. **Read test files**
   - Sees: Tests organized by concern area (cache, credentials, token lifecycle, request signing)
   - Decides: Which area is relevant to their change
   - Then: Uses test patterns as a guide for their own changes

## Functional Requirements

1. Cache round-trip tests must verify that written data can be read back identically for both token and device data
2. Cache token expiration must be verified — expired tokens must not be returned on read
3. Cache selective clearing must be verified — clearing tokens must not affect device data, and vice versa
4. Credential resolution from environment variables must be tested for both present and missing variable cases
5. Interactive shell detection must be tested for both interactive and non-interactive environments
6. The bare `raise` on line 31 of the credential utility must be replaced with an explicit error and covered by a regression test
7. Credential prompting must verify the retry loop on invalid input (empty username, invalid email format, empty password)
8. Authentication initialization must be tested for: cache-hit path (tokens in cache), password login path, and no-credentials error path
9. Token decoding must be tested for both valid tokens and missing token error case
10. Token refresh must verify the correct authentication flow parameters are sent, and must test both missing device key and missing refresh token error paths
11. Token verification and caching must be tested — valid tokens are cached after verification
12. Device setup must verify device confirmation is called with correct parameters, and device metadata is cached
13. Password login must test both the happy path and the retry-on-validation-exception path
14. Session expiry handling must verify that expired token errors clear the cache and raise a meaningful error
15. Request signing must verify the authorization header is set correctly for standard requests
16. Request signing must verify the SigV4 flow: header removal, credential fetching, signature generation, and new request creation
17. The user wrapper must be tested for: happy path with tokens, fallback to environment credentials on auth failure, and propagation of unexpected errors

## Edge Cases

1. Cache contains token data but all values are empty strings — should return empty dict, not partial data
2. Token expiration is exactly 0 seconds — boundary condition for refresh logic
3. Device key is present in cache but empty string — should be treated as missing
4. Password login gets `UserLambdaValidationException` on first attempt — must retry after delay
5. Password login gets a non-retryable `ClientError` — must propagate immediately
6. SigV4 signing receives a streaming body — must raise an error (not silently fail)
7. Token field is `None` instead of a string — must raise a clear error in the auth flow
8. `NotAuthorizedException` during token check — must clear cache and raise, not retry silently
9. Environment has `OTF_EMAIL` set but `OTF_PASSWORD` missing — must not partially authenticate
10. Non-interactive shell with no environment credentials — must raise `NoCredentialsError` (currently raises `RuntimeError`)

## Acceptance Criteria

1. `pytest tests/test_auth/ -v` passes with zero failures
2. Running `pytest tests/test_auth/ --cov=otf_api.auth --cov=otf_api.cache --cov-report=term-missing` reports 80%+ line coverage for each of auth.py, user.py, utils.py, and cache.py
3. With `OTF_EMAIL` and `OTF_PASSWORD` unset in the environment, running `pytest tests/test_auth/` still passes with zero failures
4. A test in `test_utils.py` calls the credential resolution function in a non-interactive environment with no env vars set and asserts `NoCredentialsError` is raised (not `RuntimeError`)
5. `test_otf_cognito.py` contains tests that exercise: cache-hit initialization (requirement 8), token decoding for valid and missing tokens (requirement 9), token refresh with correct parameters and both error paths (requirement 10), token verification writing to cache (requirement 11), device confirmation with correct parameters and cache write (requirement 12), password login happy path and retry-on-exception (requirement 13), and session expiry clearing cache (requirement 14)
6. `test_httpx_auth.py` contains tests that exercise: standard authorization header injection (requirement 15) and SigV4 signing flow including header removal, credential fetch, and new request creation (requirement 16)
7. `test_otf_user.py` contains tests that exercise: happy path initialization with tokens, fallback to env credentials on auth failure, and propagation of unexpected errors (requirement 17)
8. Existing `tests/test_api/` suite continues to pass unchanged
9. Pre-commit hooks (ruff, codespell) pass on all new and modified files

## Dependencies and Assumptions

- `pycognito` is installed as a dependency and provides the `Cognito` base class and `AWSSRP` authentication
- `PyJWT` is available as a transitive dependency (via `pycognito`) for crafting test tokens
- `diskcache` is installed and provides the `Cache` base class for `OtfCache`
- `pytest`, `pytest-cov`, and `respx` are already in dev dependencies — no new test dependencies needed
- `botocore` is available for SigV4 signing types (`SigV4Auth`, `AWSRequest`, `Credentials`)
- The `OtfCognito.__init__` deliberately does NOT call `super().__init__()` — tests can instantiate it without triggering pycognito's initialization
- The `@property @lru_cache` pattern on `idp_client` and `id_client` means each fresh instance has an unprimed cache — tests must use fresh instances to avoid cross-test contamination

## Architecture

### Test file structure

```
tests/test_auth/
├── __init__.py
├── conftest.py          # shared fixtures: clean_env, mock_cache, fake_tokens, mock clients
├── test_utils.py        # tests for src/otf_api/auth/utils.py
├── test_cache.py         # tests for src/otf_api/cache.py (OtfCache methods)
├── test_otf_cognito.py  # tests for src/otf_api/auth/auth.py (OtfCognito)
├── test_httpx_auth.py   # tests for src/otf_api/auth/auth.py (HttpxCognitoAuth)
└── test_otf_user.py     # tests for src/otf_api/auth/user.py (OtfUser)
```

### Mocking strategy

All mocking uses `unittest.mock.patch` — no `moto` or additional test dependencies.

**Module-level globals:**
- `otf_api.auth.auth.CACHE` → replaced with `OtfCache(tmp_path)` per test (fresh filesystem-backed cache)

**AWS service clients:**
- `OtfCognito.idp_client` → `patch.object(OtfCognito, "idp_client", new_callable=PropertyMock)` returning a `MagicMock` with pre-configured responses
- `OtfCognito.id_client` → same pattern for the identity client

**pycognito internals:**
- `pycognito.Cognito.verify_token` → no-op patch (bypasses JWKS network call)
- `pycognito.Cognito.check_token` → controlled return value
- `otf_api.auth.auth.AWSSRP` → `MagicMock` with `authenticate_user` returning crafted token dicts
- `otf_api.auth.auth.generate_hash_device` → returns test password and verifier config

**JWT tokens:**
- Craft via `jwt.encode({"sub": "test-sub", "exp": future_timestamp}, "test-secret", algorithm="HS256")` — valid structure, signature verification disabled in production code

**Environment:**
- `monkeypatch.setenv` / `monkeypatch.delenv` for `OTF_EMAIL` and `OTF_PASSWORD`
- `patch("os.isatty")` for interactive shell detection

### Bug fix

Replace `utils.py:31` bare `raise` with `raise NoCredentialsError("Unable to prompt for credentials in a non-interactive shell")`.

### Implementation phases

1. **Test infrastructure + utils.py** — conftest fixtures, env var tests, input validation, credential prompting, bare `raise` fix
2. **cache.py** — round-trip, expiry, selective clearing with `tmp_path`-backed cache instances
3. **OtfCognito core** — init paths, token decode/refresh, device setup, password login, session expiry
4. **HttpxCognitoAuth** — standard auth flow, SigV4 branch, error guards
5. **OtfUser** — init paths, credential fallback, error propagation

Each phase depends on fixtures from prior phases but is independently committable.

## Alternatives Considered

**Alternative 1: Add `moto` for full AWS mock infrastructure.** Rejected — `moto` is a heavy dependency for mocking only two boto3 client calls. `unittest.mock.patch` is sufficient and avoids adding to the dependency tree.

**Alternative 2: Refactor `OtfCognito` into `TokenManager`, `DeviceManager`, `CognitoAuthenticator` before testing.** Rejected — the class inherits from `pycognito.Cognito`, and splitting would require delegating across objects that pycognito expects to be one cohesive instance. The current structure is testable by mocking at boundaries. Refactoring can be revisited later if the class grows further.

**Alternative 3: Use `pytest-mock` instead of `unittest.mock`.** Not worth adding — `unittest.mock` is already used throughout the existing test suite and provides everything needed.

## Test Strategy

Unit tests organized by module, one test file per source file. Mock at system boundaries (AWS Cognito, boto3, JWT verification, filesystem cache, environment variables). TDD approach — one test at a time, RED → GREEN. Coverage measured via `pytest-cov` with `--cov-report=term-missing` to identify uncovered lines. Target 80%+ per file.

## Impact

**Files modified:**
- `src/otf_api/auth/utils.py` — one-line bug fix (bare `raise` → explicit `NoCredentialsError`)

**Files created:**
- `tests/test_auth/__init__.py`
- `tests/test_auth/conftest.py`
- `tests/test_auth/test_utils.py`
- `tests/test_auth/test_cache.py`
- `tests/test_auth/test_otf_cognito.py`
- `tests/test_auth/test_httpx_auth.py`
- `tests/test_auth/test_otf_user.py`

**Blast radius:** Low — only adds test files and fixes one bug. No changes to production auth flow behavior. Existing test suite unaffected.

## Open Questions

None — all questions resolved during discovery.
