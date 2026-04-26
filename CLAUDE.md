# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python library for the OrangeTheory Fitness API. Provides typed clients for bookings, member data, studios, and workouts, built on Pydantic v2, httpx, and AWS Cognito authentication.

## Development Setup

```bash
uv sync          # install all dependencies (dev group included by default)
```

## Common Commands

```bash
uv run pytest                          # run tests (requires real OTF credentials)
uv run pre-commit run --all-files      # lint + format (ruff, codespell, etc.)
uv run ruff check --fix --show-fixes   # lint only
uv run ruff format                     # format only
uv build                               # build wheel and sdist
uv run python scripts/generate_openapi.py  # generate OpenAPI schema from Pydantic models
```

## Testing

Tests require real OrangeTheory credentials. Set `OTF_EMAIL` and `OTF_PASSWORD` environment variables before running pytest.

## Code Style

- **Line length**: 120 (configured in `ruff.toml`)
- **Docstrings**: Google-style
- **Quotes**: Double quotes
- **Indentation**: 4 spaces
- All Ruff rules are auto-fixable (`fixable = ["ALL"]`)
- Pre-commit hooks enforce ruff check, ruff format, codespell, and standard file hygiene

## Architecture Notes

- **Source layout**: `src/otf_api/` with sub-packages for `api/`, `auth/`, `models/`
- **Auth**: Cognito client ID, region, user pool ID, and identity pool ID are hardcoded in `auth/auth.py` (extracted from the OTF Android app)
- **Models**: All Pydantic models inherit from `OtfItemBase` which sets `extra="ignore"` to handle upstream API schema changes gracefully
- **Caching**: Disk-based response caching via `diskcache`, persists across sessions
- **Logging**: Auto-initialized on module import via `coloredlogs`; controlled by `OTF_LOG_LEVEL` env var (default: INFO)

## Git Workflow

- Feature branches for new work
- Version bumps via `bump-my-version` (configured in `.bumpversion.toml`)
- CI runs tests on Python 3.11 and 3.12, plus pre-commit checks
- Releases triggered by `v*.*.*` tags; publishes to PyPI via trusted publishing
