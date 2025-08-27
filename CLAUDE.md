# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **otf-api**, an unofficial Python API client for OrangeTheory Fitness APIs. The library provides access to OTF APIs for retrieving workouts, performance data, class schedules, studio information, and bookings.

**Important**: This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness. It may break if OrangeTheory changes their services.

## Development Commands

### Monorepo Commands (from root)
- **Install all dependencies**: `npm run install:python && npm run install:typescript`
- **Build everything**: `npm run build` (includes schema generation)
- **Test everything**: `npm test` (includes generation validation)
- **Lint everything**: `npm run lint`
- **Generate schema**: `npm run generate-schema` (Python models → OpenAPI)
- **Generate TypeScript types**: `npm run generate-ts` (OpenAPI → TypeScript)
- **Full sync**: `npm run sync` (Python → OpenAPI → TypeScript)
- **Validate pipeline**: `npm run validate` (sync + test generation)

### Python Package Management
- Uses **uv** for dependency management (see `python/uv.lock`)
- Install dependencies: `cd python && uv sync`
- Add dependencies: `cd python && uv add <package>`

### Python Code Quality
- **Lint and format**: `cd python && uv run ruff check --fix && uv run ruff format`
- **Type checking**: Uses mypy via pre-commit hooks
- **Run tests**: `cd python && uv run pytest`
- **Run single test**: `cd python && uv run pytest tests/test_file.py::test_function`
- **Test schema generation**: `cd python && uv run pytest tests/test_schema_generation.py -v`

### TypeScript Code Quality
- **Install dependencies**: `cd typescript && npm install`
- **Build**: `cd typescript && npm run build`
- **Test**: `cd typescript && npm test`
- **Lint**: `cd typescript && npm run lint:fix`
- **Type check**: `cd typescript && npm run type-check`
- **Test generation pipeline**: `cd typescript && npm run test -- schema-generation.test.ts`

### Pre-commit Hooks
- Setup: `uv run pre-commit install`
- Run manually: `uv run pre-commit run --all-files`
- Includes ruff (linting/formatting), codespell, and standard hooks

### Documentation
- Build docs: Uses Sphinx (see `source/` directory)
- Documentation available at: https://otf-api.readthedocs.io/en/stable/

## Architecture

### Monorepo Structure
- **Python Library** (`python/`): Source of truth with comprehensive Pydantic models
- **TypeScript Library** (`typescript/`): Auto-generated client with custom improvements  
- **Shared Schema** (`schema/`): OpenAPI specification generated from Python models
- **Generation Scripts** (`scripts/`): Schema generation and sync utilities

### Python Core Structure  
- **Main API Class**: `python/src/otf_api/api/api.Otf` - Main entry point that orchestrates all functionality
- **Authentication**: `python/src/otf_api/auth` - Handles OTF authentication via AWS Cognito (`pycognito`)
- **API Clients**: `python/src/otf_api/api.*` - Low-level HTTP clients for different API endpoints
- **Models**: `python/src/otf_api/models.*` - Pydantic models for all data structures (source of truth)
- **Caching**: `python/src/otf_api/cache` - Disk-based caching using `diskcache`

### TypeScript Structure
- **Generated Types**: `typescript/src/generated/` - Auto-generated from OpenAPI schema
- **API Clients**: `typescript/src/api/` - Custom TypeScript client implementations
- **Authentication**: `typescript/src/auth/` - Cognito and device authentication
- **Caching**: `typescript/src/cache/` - Multiple cache implementations
- **Models Export**: `typescript/src/models.ts` - Re-exports generated types with aliases

### Schema Generation Pipeline
1. **Python Models** → `scripts/generate_openapi.py` → **OpenAPI YAML**
2. **OpenAPI YAML** → `openapi-typescript` → **TypeScript Types**
3. **Tests validate** each step of the pipeline for consistency
4. **Sync validation** ensures Python models remain source of truth

### Sync Validation Requirements
- **Python models are the ONLY source of truth** - never use OrangeTheory API field names as source
- **Field name consistency**: Python field names (`member_uuid`) must be preserved through the entire pipeline
- **Automated validation**: Run `uv run python scripts/validate_ts_sync.py` to check sync status
- **Pre-commit validation**: Schema generation and sync validation should be part of CI/CD
- **TypeScript transformation**: All API transformation code must match generated types exactly
- **No type casting workarounds**: TypeScript code should not use `as any` - fix type mismatches instead

### API Organization
The API is organized into 4 main domains:
- **Bookings** (`otf_api.api.bookings`): Class booking, cancellation, waitlists
- **Members** (`otf_api.api.members`): Member details, memberships, purchases  
- **Studios** (`otf_api.api.studios`): Studio information, services, locations
- **Workouts** (`otf_api.api.workouts`): Performance data, stats, challenge tracking

### Model Architecture
- **Base Model**: `otf_api.models.base.OtfItemBase` extends Pydantic `BaseModel` with common config
- **Domain Models**: Organized by domain (bookings, members, studios, workouts)
- **Mixins**: `otf_api.models.mixins` - Shared model behaviors
- **Enums**: Domain-specific enums in each model package

### Client Pattern
Each API domain follows this pattern:
- `*Api` class: High-level interface with business logic and data enrichment
- `*Client` class: Low-level HTTP client handling raw API requests
- Models: Pydantic classes for request/response serialization

### Authentication Flow
1. Uses AWS Cognito for OTF authentication
2. Credentials can be provided via:
   - `OtfUser` object passed to `Otf()` constructor
   - Environment variables: `OTF_EMAIL` and `OTF_PASSWORD`
   - Interactive prompts if no credentials provided
3. Tokens are cached for reuse

### Key Dependencies
- **pydantic**: Data validation and serialization (all models inherit from `OtfItemBase`)
- **httpx**: HTTP client for API requests
- **pycognito**: AWS Cognito authentication
- **attrs**: Used for some data classes
- **diskcache**: Disk-based caching
- **pendulum**: Date/time handling

## Code Style
- **Line length**: 120 characters
- **Docstring style**: Google format
- **Import sorting**: Handled by ruff
- **Type hints**: Required (enforced by ruff ANN rules)
- Uses ruff for linting with extensive rule set (see `ruff.toml`)

## CRITICAL: Code Quality Requirements
**ALWAYS validate code matches CI exactly by running:**
```bash
cd python
uv run ruff check --output-format=github
uv run ruff format --check
```

**To fix issues before validation:**
```bash
cd python
uv run ruff check --fix
uv run ruff format
```

**CI Requirements (MUST PASS):**
- `uv run ruff check --output-format=github` - Must show no errors
- `uv run ruff format --check` - Must show "X files already formatted" (no "would reformat")

**Common errors to avoid:**
- **NO blank lines with whitespace** - Use completely empty lines
- **NO unused noqa directives** - Only use `noqa` when actually needed  
- **NO trailing whitespace** - Ruff will catch and fix these
- **ALL functions must have type annotations** - Required by ANN rules
- **ALL functions must have docstrings** - Google format required

**Workflow for adding code:**
1. Write the code
2. Fix issues: `uv run ruff check --fix && uv run ruff format`  
3. Validate against CI: `uv run ruff check --output-format=github && uv run ruff format --check`
4. Both commands must pass with no errors or "would reformat" messages

**Never commit code that fails CI validation commands**

## Environment Variables
- `OTF_EMAIL`: OrangeTheory email for authentication
- `OTF_PASSWORD`: OrangeTheory password for authentication  
- `OTF_LOG_LEVEL`: Logging level (default: INFO)

## Testing
- Uses pytest framework
- Test files in `tests/` directory
- Run with: `uv run pytest`
- Currently has minimal test coverage - primarily model validation tests

## Authentication Context
This library authenticates with OrangeTheory's private APIs using member credentials. Handle authentication data securely and never commit credentials to the repository.