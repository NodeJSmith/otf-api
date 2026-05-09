# Authentication

The `otf-api` library authenticates against OrangeTheory's AWS Cognito backend. All token management, refresh, and device registration is handled automatically.

## Credential Setup

There are three ways to provide credentials, checked in this order:

### 1. Direct credentials

Pass your email and password directly when creating the client:

```python
from otf_api import Otf
from otf_api.auth import OtfUser

user = OtfUser(username="you@example.com", password="your-password")
otf = Otf(user=user)
```

### 2. Environment variables

Set `OTF_EMAIL` and `OTF_PASSWORD` in your environment:

```bash
export OTF_EMAIL="you@example.com"
export OTF_PASSWORD="your-password"
```

Then create the client without arguments:

```python
from otf_api import Otf

otf = Otf()  # reads from environment
```

### 3. Interactive prompt

If no credentials are found and the session is interactive (TTY attached), the library prompts for your email and password at runtime. This is useful for quick scripts and notebooks.

```python
from otf_api import Otf

otf = Otf()  # prompts if env vars are missing
```

!!! warning
    The interactive prompt requires a TTY. In non-interactive environments (CI, cron jobs, Docker containers), you must use environment variables or direct credentials.

## How Auth Works

When you create an `Otf` client, the library:

1. Checks the disk cache for valid tokens from a previous session
2. If cached tokens exist and are not expired, uses them directly
3. If no valid cache exists, authenticates with Cognito using the SRP (Secure Remote Password) protocol
4. Stores the resulting tokens in the disk cache for future sessions

All of this happens transparently — you never need to manage tokens yourself.

## Token Caching

Tokens are persisted to disk using `diskcache`, stored in a platform-appropriate cache directory (e.g., `~/.cache/otf-api/v2/` on Linux). This means:

- Subsequent script runs reuse existing tokens without re-authenticating
- Tokens automatically expire from the cache when they become invalid
- The cache is versioned by major library version to avoid conflicts during upgrades

### Clearing the cache

If you encounter auth issues, clear the cache:

```python
from otf_api.cache import clear_cache

clear_cache()
```

This removes both token and device data, forcing a fresh login on next use.

## Device Key Management

The Cognito user pool used by OrangeTheory requires device confirmation. On first authentication, the library:

1. Receives a device key from Cognito as part of the auth response
2. Confirms the device using a cryptographic verifier
3. Caches the device key, group key, and password for future sessions

The device key is required for token refresh to work. Without it, refresh attempts fail with `NOT_AUTHORIZED`.

!!! note
    The library confirms devices but does not "remember" them (no MFA bypass). This matches the behavior of the official OTF mobile app.

## Token Refresh

Access tokens have a limited lifetime (typically 1 hour). The library handles refresh automatically:

- Before each API request, the token expiration is checked
- If the access token has expired, it is silently refreshed using the stored refresh token and device key
- If the refresh token itself has expired, the cache is cleared and a `NoCredentialsError` is raised

You do not need to handle refresh logic in your code.

## The OtfUser Class

`OtfUser` is the primary authentication object. It wraps the Cognito interaction and exposes:

| Attribute | Description |
|-----------|-------------|
| `cognito_id` | The Cognito subject ID (`sub` claim) |
| `member_uuid` | The OTF member UUID (used in API calls) |
| `email_address` | The authenticated user's email |
| `httpx_auth` | The HTTPX auth handler attached to API requests |

You can pass an `OtfUser` instance to `Otf()` or let the client create one internally.

## Troubleshooting

!!! danger "Wrong credentials"
    If you see `NotAuthorizedException` or `UserNotFoundException`, double-check your email and password. The email is case-sensitive.

!!! tip "Stale cache"
    If authentication worked previously but now fails with token errors, clear the cache:
    ```python
    from otf_api.cache import clear_cache
    clear_cache()
    ```
    Then retry. This forces a full re-authentication.

!!! warning "Non-interactive environments"
    If you see `NoCredentialsError: Unable to prompt for credentials in a non-interactive shell`, ensure `OTF_EMAIL` and `OTF_PASSWORD` environment variables are set.
