# Design: Documentation Overhaul — Sphinx to MkDocs-Material

**Date:** 2026-05-09
**Status:** approved
**Scope-mode:** hold
**Research:** /tmp/claude-mine-define-research-4LSHpm/brief.md

## Problem

The library's documentation is sparse and fragmented, creating three compounding problems:

1. **Users can't self-serve.** There is no getting started guide, no authentication walkthrough, and no troubleshooting page. Users open GitHub issues asking basic questions the docs should answer — Pydantic validation errors from upstream API changes, workout count mismatches, 404 errors after version upgrades, and credential setup confusion.

2. **Contributors face friction.** The library's four-domain architecture (bookings, workouts, studios, members), authentication flow, caching layer, and exception hierarchy are undocumented. Understanding the codebase requires reading source code — there is no architecture overview or design explanation.

3. **Sparse docs hurt credibility.** The current documentation site has a single landing page with one code snippet, four raw Python file renders, and auto-generated API stubs. This does not meet the quality bar that developers expect from a library they will depend on, reducing adoption.

The current documentation tooling (Sphinx with RST) adds maintenance friction — RST is harder to write and review than Markdown, discouraging content contributions.

## Goals

- A new user can go from `pip install` to a successful API call using only the documentation (no source code reading required)
- Every public class, method, property, enum, and exception is documented in an auto-generated API reference with type annotations, descriptions, and cross-references
- The documentation site is navigable, searchable, and visually polished — on par with well-regarded Python libraries
- Common user pain points (auth setup, validation errors, booking edge cases) are addressed with dedicated troubleshooting content
- Guide content covers all four API domains with explanatory prose and code examples

## Non-Goals

- **Versioned documentation** — only the latest version will be published
- **Contributor guide** — no CONTRIBUTING.md or contributor-facing documentation
- **Interactive/runnable examples** — code examples are static (the API requires real OTF credentials)

## User Scenarios

### New User: OTF member wanting to automate class bookings

- **Goal:** Book OTF classes programmatically
- **Context:** Found the library on PyPI or GitHub, has Python experience but no knowledge of the OTF API

#### First-time setup

1. **Reads the landing page**
   - Sees: What the library does, installation command, link to getting started guide
   - Decides: Whether this library fits their needs
   - Then: Clicks through to getting started guide

2. **Follows the getting started guide**
   - Sees: Step-by-step instructions for installing, setting credentials, and making a first API call
   - Decides: Which credential method to use (env vars vs direct)
   - Then: Successfully initializes the client and retrieves their member info

3. **Explores domain guides**
   - Sees: Bookings guide with class search, filtering, and booking examples
   - Decides: Which API methods to use for their use case
   - Then: Books a class programmatically

#### Troubleshooting a problem

1. **Encounters a Pydantic validation error**
   - Sees: Error message with field names and types
   - Decides: Checks troubleshooting page
   - Then: Finds explanation that upstream API schema changes can cause this, with workaround

### Returning User: Checking API reference for a specific method

- **Goal:** Find the signature and behavior of a specific method
- **Context:** Already using the library, needs to look up parameters or return types

#### API lookup

1. **Uses site search or navigation**
   - Sees: Organized API reference with search functionality
   - Decides: Navigates to the relevant domain section
   - Then: Finds the method with full signature, docstring, parameters, return type, and exceptions

## Functional Requirements

- **FR#1** The documentation site renders from Markdown source files using a modern static site generator with search, navigation tabs, and code syntax highlighting
- **FR#2** The API reference is auto-generated from source code docstrings at build time, requiring no manual synchronization
- **FR#3** Data model documentation renders field names, types, default values, and descriptions extracted from source code field metadata
- **FR#4** The documentation deploys automatically on push to the default branch via webhook integration with the existing hosting platform
- **FR#5** A getting started guide walks a new user from installation through authentication to a first successful API call
- **FR#6** Domain-specific guides cover bookings/classes, workouts/stats, studios, challenges, and members with explanatory prose and code examples
- **FR#7** An authentication guide explains credential setup, token lifecycle, caching behavior, and the device key flow
- **FR#8** An error handling guide documents the exception hierarchy with descriptions, common causes, and handling patterns
- **FR#9** A troubleshooting page addresses known user pain points: validation errors from upstream API changes, workout count mismatches, authentication failures, and version upgrade issues
- **FR#10** All custom exception classes are exported as part of the public API so users can catch specific error types
- **FR#11** An architecture overview explains the four-domain API structure, authentication flow, caching layer, and model hierarchy
- **FR#12** The landing page provides a concise overview, installation instructions, and navigation to all major documentation sections
- **FR#13** A legal disclaimer footer appears on every documentation page noting the project is not affiliated with OrangeTheory Fitness
- **FR#14** All public classes, methods, properties, and enums have docstrings following a consistent style convention with parameter descriptions, return types, and raised exceptions

## Edge Cases

- **Pydantic models with excluded fields**: Models have fields marked `exclude=True, repr=False` (internal MindBody attributes). These must not appear in the API reference — they would confuse users with irrelevant internal details.
- **Multiple inheritance on models**: Models inherit from both `OtfItemBase` and `ApiMixin`. The mixin's runtime methods (`set_api`, `create`, `raise_if_api_not_set`) are internal and should not clutter individual model documentation.
- **Dual booking API versions**: Both `Booking`/`get_bookings` (old) and `BookingV2`/`get_bookings_new` (new) APIs exist. Guides must clearly direct users to the current API while the reference documents both.
- **Import side effects**: The package's `__init__.py` calls `_setup_logging()` and `coloredlogs.install()` on import. The doc build tool must not trigger these side effects.
- **Computed fields**: Models use `@computed_field` which needs rendering alongside regular fields in the API reference.
- **Alias fields**: Models use `validation_alias`, `AliasPath`, and `AliasChoices`. The reference should show the Python attribute name, not the alias.

## Acceptance Criteria

- **AC#1** Running the documentation build locally produces a complete site with no errors or warnings (maps to FR#1, FR#2, FR#3)
- **AC#2** The API reference contains entries for every public class, method, and enum exported by the package — verified by comparing reference page count against the `__all__` exports (maps to FR#2, FR#14)
- **AC#3** Pydantic model pages show field names, types, defaults, and descriptions without showing internal Pydantic methods (`model_dump`, `model_validate`, etc.) or `exclude=True` fields (maps to FR#3)
- **AC#4** A push to the default branch triggers an automatic documentation build and deployment to the existing hosting URL (maps to FR#4)
- **AC#5** A user following only the getting started guide can install the library, configure credentials, and make a successful API call (maps to FR#5)
- **AC#6** Each of the five domain guides (bookings, workouts, studios, challenges, members) contains at least one complete code example with explanatory context (maps to FR#6)
- **AC#7** The exception classes `OtfError`, `OtfRequestError`, `BookingError`, `AlreadyBookedError`, `ConflictingBookingError`, and all other custom exceptions are importable from `otf_api.exceptions` and documented in the error handling guide (maps to FR#8, FR#10)
- **AC#8** The troubleshooting page addresses at least: Pydantic validation errors, authentication failures, and workout count discrepancies (maps to FR#9)
- **AC#9** The disclaimer footer renders on every page of the deployed site (maps to FR#13)
- **AC#10** No Sphinx artifacts remain in the repository after migration (RST files, conf.py, Sphinx dependencies) (maps to FR#1)
- **AC#11** The authentication guide covers credential setup via environment variables, direct parameters, and `OtfUser`, plus explains token caching and refresh behavior (maps to FR#7)
- **AC#12** The architecture overview names all four API domain sub-clients, the authentication flow, and the caching layer, with enough context that a new reader understands the module structure without reading source code (maps to FR#11)
- **AC#13** The landing page contains an installation command, a brief description of what the library does, and links to the getting started guide, domain guides, and API reference (maps to FR#12)

## Key Constraints

- **Do not use Sphinx or RST** — the migration is to MkDocs-Material with Markdown. No hybrid approach.
- **Do not trigger package imports during doc builds** — the doc tool must use static AST parsing, not runtime import, to avoid side effects from the package's `__init__.py` logging setup.
- **Do not document `*_client.py` files** — these are internal HTTP transport layers, not public API.
- **Do not include the `anonymize/` sub-package in user-facing guides** — it is a developer utility for test fixture generation, not a core user feature. It may appear in the API reference but should not have guide content.
- **Model the docs structure and MkDocs configuration after the hassette project** (`/home/jessica/source/hassette`) — same author, same hosting, proven patterns.

## Dependencies and Assumptions

- **ReadTheDocs** continues to support MkDocs builds via webhook integration (well-established feature)
- **mkdocstrings[python]** with griffe parses source code via AST (no imports), avoiding `coloredlogs.install()` side effects
- **griffe-pydantic** correctly renders `Field(description=...)`, handles `OtfItemBase` custom base class, and can filter `exclude=True` fields — this assumption needs validation via local prototype before committing to guide writing
- **Hassette's mkdocs.yml** provides a working template that can be adapted for otf-api's simpler scope
- **Existing example scripts** (`examples/*.py`) contain reusable code patterns for guide content
- **CHANGELOG.md** at repo root (generated by release-please) can be symlinked into the docs directory

## Architecture

### Tooling stack

Replace the Sphinx ecosystem with MkDocs-Material:

| Component | Current (Sphinx) | New (MkDocs) |
|---|---|---|
| Site generator | `sphinx>=8.3.0` | `mkdocs>=1.6.0` + `mkdocs-material>=9.6.0` |
| Theme | `furo` | Material (built into mkdocs-material) |
| API doc extraction | `sphinx.ext.autodoc` | `mkdocstrings[python]>=0.25.0` |
| Pydantic rendering | `autodoc-pydantic>=2.2.0` | `griffe-pydantic>=1.0.0` |
| Docstring style | `sphinx.ext.napoleon` | Built into mkdocstrings (Google style) |
| Code cross-refs | `sphinx.ext.viewcode` | `mkdocs-autorefs>=0.5.0` |
| Reference generation | 13 hand-maintained RST stubs | `mkdocs-gen-files>=0.5.0` + `tools/gen_ref_pages.py` |
| Navigation | RST toctree | `mkdocs-literate-nav>=0.6.1` + `SUMMARY.md` |
| Markdown extensions | N/A (RST) | `pymdown-extensions>=10.8.1` |

### Configuration files

**`mkdocs.yml`** (new) — adapted from hassette's 164-line config:
- Site metadata pointing to `https://otf-api.readthedocs.io/`
- Material theme with navigation tabs, instant navigation, code copy, search
- Plugin chain: search → gen-files → literate-nav → autorefs → mkdocstrings
- mkdocstrings Python handler with `paths: [src]`, `docstring_style: google`, griffe-pydantic extension
- Markdown extensions: admonitions, code highlighting, tabbed content, superfences
- Footer with disclaimer (via `extra` config or custom CSS override from `docs/_static/custom.css`)

**`tools/gen_ref_pages.py`** (rewrite of `scripts/gen_ref_pages.py`) — adapted from hassette's allowlist-based approach:
- Uses `PUBLIC_MODULES` frozenset defining the exact modules to document (see research brief for full list)
- Generates per-module `.md` files with `::: module.path` directives under `docs/reference/`
- Writes `reference/SUMMARY.md` for literate-nav sidebar
- Excludes `*_client.py`, `anonymize/`, `cache.py`, internal utilities
- Moved to `tools/` directory to match hassette convention (keep `scripts/` for user-facing scripts)

**`.readthedocs.yaml`** (modify) — change `sphinx:` section to `mkdocs:`:
```yaml
mkdocs:
  configuration: mkdocs.yml
  fail_on_warning: true
```
Keep the existing `uv sync --group docs` build jobs.

**`pyproject.toml`** (modify) — replace docs dependency group:
```toml
[dependency-groups]
docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.6.0",
    "mkdocs-gen-files>=0.5.0",
    "mkdocs-literate-nav>=0.6.1",
    "mkdocs-autorefs>=0.5.0",
    "mkdocstrings[python]>=0.25.0",
    "griffe-pydantic>=1.0.0",
    "pymdown-extensions>=10.8.1",
]
```

### Docs directory structure

```
docs/
├── index.md                           # Landing page: overview, install, quick links
├── getting-started/
│   └── index.md                       # Zero-to-API-call walkthrough
├── guides/
│   ├── authentication.md              # Cognito auth, env vars, token caching, OtfUser
│   ├── bookings.md                    # Classes, bookings, filters, ratings
│   ├── workouts.md                    # Workouts, telemetry, stats, body composition
│   ├── studios.md                     # Studio search, details, favorites
│   ├── challenges.md                  # Challenge tracker, benchmarks
│   ├── members.md                     # Member details, notifications, purchases
│   └── error-handling.md              # Exception hierarchy, retry behavior, common errors
├── architecture/
│   └── index.md                       # Module map, data flow, design decisions
├── troubleshooting.md                 # Known issues, FAQs, env var reference
├── _static/
│   └── custom.css                     # Disclaimer footer styling
├── CHANGELOG.md -> ../../CHANGELOG.md # Symlink to repo root
└── reference/                         # Auto-generated at build time by gen_ref_pages.py
    └── SUMMARY.md                     # Auto-generated navigation
```

### Pydantic model rendering strategy

Replace the 30-entry `PYDANTIC_IGNORE_FIELDS` exclusion list in `source/conf.py` with griffe-pydantic's template-level rendering. Configure mkdocstrings filters in `mkdocs.yml`:

```yaml
options:
  filters:
    - "!^_"            # hide private members
    - "!^model_"       # hide Pydantic model_* methods
  inherited_members: false  # hide ApiMixin methods on models
```

For `exclude=True` fields: test griffe-pydantic's handling locally. If it renders them, add a custom filter or use `show_if_no_docstring: false` to suppress undescribed internal fields.

### Source code changes

- **`src/otf_api/__init__.py`**: Add exceptions to `__all__` exports (or add `from otf_api.exceptions import *` with explicit `__all__` in `exceptions.py`)
- **`src/otf_api/exceptions.py`**: Add `__all__` listing all 11 exception classes (the 12th, `NoCredentialsError`, lives in `auth/auth.py` and is internal)
- **Docstring gaps**: Fill remaining docstring gaps on public classes, methods, properties, and enums across the codebase (~40% of public API surface needs new or improved docstrings)
- **Pydantic field descriptions**: Add `Field(description=...)` to fields that lack descriptions in user-facing models

### Files to delete after migration

- `source/` directory (all RST files, conf.py, _static/, _templates/)
- `scripts/gen_ref_pages.py` (replaced by `tools/gen_ref_pages.py`)
- Sphinx dependencies from pyproject.toml (replaced by MkDocs deps)

## Alternatives Considered

### Keep Sphinx, just add content

Stay on the current Sphinx/Furo stack and focus effort on writing guide content in RST.

**Rejected because:** RST is higher friction for writing and reviewing documentation. The project already has an abandoned MkDocs migration attempt (`scripts/gen_ref_pages.py`), indicating a prior desire to move. The hassette project provides a proven MkDocs-Material template by the same author, making migration low-risk. The Sphinx setup's `PYDANTIC_IGNORE_FIELDS` hack (30+ entries) is fragile and would need constant maintenance as Pydantic evolves.

### MkDocs-Material without griffe-pydantic

Use mkdocstrings[python] with manual filters instead of the griffe-pydantic extension.

**Rejected because:** Without griffe-pydantic, Pydantic model fields would render as plain class attributes without structured descriptions, required/optional badges, or validator documentation. The `Field(description=...)` values already present in the source code would be invisible in the docs. Manually recreating this rendering via mkdocstrings options would be fragile and incomplete.

## Test Strategy

- **Local build verification**: Run `mkdocs build --strict` and `mkdocs serve` to verify all pages render without errors or warnings
- **Pydantic rendering validation**: Verify that model pages show field descriptions, hide `exclude=True` fields, and suppress internal Pydantic methods — spot-check against `Booking`, `OtfClass`, `MemberDetail`, and `Workout` models
- **Cross-reference validation**: Verify that `::: module.path` directives resolve correctly and inter-page links work
- **RTD deployment verification**: Push to a branch and verify RTD webhook triggers a successful build
- **Content review**: Each guide page reviewed for accuracy against the current API behavior
- **Search functionality**: Verify site search returns relevant results for common queries ("book a class", "workout history", "authentication")

## Documentation Updates

- **README.md**: Update the documentation link if the URL structure changes (currently `https://otf-api.readthedocs.io/en/stable/`)
- **CLAUDE.md**: Update the "Common Commands" section to replace Sphinx build commands with MkDocs equivalents (`mkdocs serve`, `mkdocs build`)

## Impact

### Files modified
- `pyproject.toml` — docs dependency group replacement + exceptions `__all__` in source
- `.readthedocs.yaml` — Sphinx → MkDocs configuration
- `src/otf_api/__init__.py` — add exceptions to exports
- `src/otf_api/exceptions.py` — add `__all__`
- ~30-40 source files for docstring improvements across `api/`, `models/`, `auth/`

### Files created
- `mkdocs.yml` — new MkDocs-Material configuration
- `tools/gen_ref_pages.py` — new API reference generator
- `docs/` directory — ~12-15 new Markdown guide pages
- `docs/_static/custom.css` — disclaimer footer styling

### Files deleted
- `source/` directory — all 20+ Sphinx RST files, conf.py, templates, static assets
- `scripts/gen_ref_pages.py` — replaced by `tools/gen_ref_pages.py`

### Blast radius
- Documentation hosting (ReadTheDocs) will briefly show the old Sphinx site until the first MkDocs build deploys
- No runtime code changes beyond exception exports and docstring additions
- No changes to test infrastructure, CI workflows, or package build process

## Open Questions

*None — all questions resolved during discovery.*
