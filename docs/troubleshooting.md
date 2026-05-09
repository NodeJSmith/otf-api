# Troubleshooting

Common issues and their solutions when working with the otf-api library.

## Pydantic Validation Errors

!!! warning "Symptom"
    `ValidationError` when calling `get_workouts()`, `get_performance_summaries()`, or other data-fetching methods.

**Cause:** The upstream OTF API occasionally changes its response schema. The library uses
`extra="ignore"` on all models to handle new fields gracefully, but type changes or removed
required fields can still trigger validation errors.

**Solution:**

1. Update to the latest version: `pip install --upgrade otf-api`
2. If the error persists, [open a GitHub issue](https://github.com/NodeJSmith/otf-api/issues/new) with the full traceback so the models can be updated.

## Authentication Failures

!!! warning "Symptom"
    Login fails, token refresh fails, or you see `NoCredentialsError`.

**Cause:** Incorrect credentials, expired cached tokens, or a corrupted device key cache.

**Solution:**

1. Verify your credentials are correct:
    ```python
    import os
    print(os.environ.get("OTF_EMAIL"))
    print(os.environ.get("OTF_PASSWORD"))
    ```
2. Clear the cache to remove stale tokens and device keys:
    ```python
    from otf_api.cache import clear_cache
    clear_cache()
    ```
3. Retry authentication.

!!! tip
    If you only want to clear tokens (keeping device registration intact):
    ```python
    from otf_api.cache import get_cache
    cache = get_cache()
    cache.clear_tokens()
    ```

## Workout Count Discrepancies

!!! warning "Symptom"
    `get_workouts()` returns fewer workouts than the OTF app shows.

**Cause:** The API may not return all historical data, especially older workouts.

**Solution:**

- Use date range filtering to query specific periods.
- The API response is the source of truth for what the backend exposes; the mobile app may display locally cached or aggregated data.

## 404 Errors After Version Upgrades

!!! warning "Symptom"
    `ResourceNotFoundError` or `404 Not Found` after upgrading the library.

**Cause:** The underlying OTF API endpoints change periodically. A new library version may
target updated endpoints that your cached state or older code paths don't match.

**Solution:**

1. Ensure you are on the latest release: `pip install --upgrade otf-api`
2. Check the [CHANGELOG](https://github.com/NodeJSmith/otf-api/releases) for breaking changes.
3. Clear your cache in case stale data is involved:
    ```python
    from otf_api.cache import clear_cache
    clear_cache()
    ```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OTF_EMAIL` | OrangeTheory Fitness account email address |
| `OTF_PASSWORD` | OrangeTheory Fitness account password |
| `OTF_LOG_LEVEL` | Logging verbosity (default: `INFO`) |

## Cache Management

The library uses [`diskcache`](https://grantjenks.com/docs/diskcache/) for persistent caching
of authentication tokens and device registration data. The cache directory is determined by
[`platformdirs.user_cache_dir`](https://platformdirs.readthedocs.io/en/latest/) and is
versioned by the library's major version (e.g., `otf-api/v1/`).

**Typical locations:**

- Linux: `~/.cache/otf-api/v1/`
- macOS: `~/Library/Caches/otf-api/v1/`
- Windows: `C:\Users\<user>\AppData\Local\otf-api\Cache\v1\`

**Clearing the cache:**

```python
from otf_api.cache import clear_cache

# Clear everything (tokens + device data)
clear_cache()
```

!!! tip "Selective cache clearing"
    ```python
    from otf_api.cache import get_cache

    cache = get_cache()
    cache.clear_tokens()       # Remove only auth tokens
    cache.clear_device_data()  # Remove only device registration
    ```
