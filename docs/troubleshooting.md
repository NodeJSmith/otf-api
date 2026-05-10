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
2. If the error persists, [open a GitHub issue](https://github.com/NodeJSmith/otf-api/issues/new) with the full traceback and [anonymized response data](#filing-a-bug-report-with-anonymized-data) so the models can be updated.

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

If the problem persists after clearing the cache, [file a bug report](#filing-a-bug-report-with-anonymized-data) with the full traceback.

## Workout Count Discrepancies

!!! warning "Symptom"
    `get_workouts()` returns fewer workouts than the OTF app shows.

**Cause:** The API may not return all historical data, especially older workouts.

**Solution:**

- Use date range filtering to query specific periods.
- The API response is the source of truth for what the backend exposes; the mobile app may display locally cached or aggregated data.

If you believe the data is incorrect, [file a bug report](#filing-a-bug-report-with-anonymized-data) with the date range and expected vs. actual count.

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

If the error persists, [file a bug report](#filing-a-bug-report-with-anonymized-data) with the URL from the `OtfRequestError` and the library version.

## Filing a Bug Report with Anonymized Data

When reporting issues — especially validation errors or unexpected API responses — including the raw data dramatically speeds up debugging. The library has a built-in anonymization pipeline that strips all PII (names, emails, member IDs, biometrics, etc.) while preserving the data structure.

### Capture mode

Set `OTF_ANONYMIZE_RESPONSES=true` to automatically capture and anonymize every API response to disk as you use the library:

```bash
export OTF_ANONYMIZE_RESPONSES=true
```

```python
from otf_api import Otf

otf = Otf()
# Use the library normally — all responses are captured and anonymized
workouts = otf.workouts.get_workouts()
```

Anonymized JSON files are written to your platform's cache directory under `otf-api/debug/` (e.g., `~/.cache/otf-api/debug/` on Linux). Override with `OTF_ANONYMIZE_OUTPUT_DIR`. Attach the relevant files to your GitHub issue.

### Manual anonymization

For finer control, use the `Anonymizer` directly:

```python
from otf_api import AnonymizeConfig, Anonymizer
from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import FIELD_MAPPINGS

config = AnonymizeConfig(seed=42, strictness="mask")
generators = FakeDataGenerators(seed=42)
anonymizer = Anonymizer(config=config, generators=generators, mappings=FIELD_MAPPINGS)

# Anonymize a single response dict
anonymized = anonymizer.anonymize_dict(raw_response_data)
```

### What gets anonymized

The pipeline handles 110+ field types across these categories:

| Category | Examples |
|----------|----------|
| Identity | member UUIDs, cognito IDs, person IDs |
| Contact | names, emails, phone numbers, addresses |
| Personal | birthdate, gender, age |
| Biometric | weight, height, body composition, heart rate |
| Financial | credit card last 4, payment references |
| Studio | studio names, addresses, coordinates |
| Security | auth tokens (replaced with `REDACTED`) |

The anonymizer maintains **referential integrity** — the same real value always maps to the same fake value, so relationships in the data are preserved. Body composition fields are scaled together to keep physiological ratios consistent, and heart rate zones are recalculated from the anonymized max HR.

!!! tip
    Use `strictness="mask"` to replace any unknown fields with `__MASKED__`. This is the safest option for bug reports since it catches fields the anonymizer doesn't explicitly know about.
