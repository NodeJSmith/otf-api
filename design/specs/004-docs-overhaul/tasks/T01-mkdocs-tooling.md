---
task_id: "T01"
title: "Set up MkDocs-Material tooling and infrastructure"
status: "planned"
depends_on: []
implements: ["FR#1", "FR#2", "FR#3", "FR#4", "FR#13", "AC#1", "AC#3", "AC#4", "AC#9"]
---

## Summary
Set up the complete MkDocs-Material documentation infrastructure: create `mkdocs.yml`, rewrite `gen_ref_pages.py`, update `.readthedocs.yaml` and `pyproject.toml`, and add the disclaimer footer. After this task, `mkdocs serve` should render the auto-generated API reference with Pydantic model fields correctly, and the site should deploy via ReadTheDocs webhook.

## Prompt
Create the MkDocs-Material documentation infrastructure, using the hassette project at `/home/jessica/source/hassette` as the reference implementation.

### 1. Create `mkdocs.yml` at repo root
Adapt from hassette's `mkdocs.yml` at `/home/jessica/source/hassette/mkdocs.yml`. Key settings:
- `site_name: otf-api`
- `site_url: https://otf-api.readthedocs.io/`
- `repo_url: https://github.com/NodeJSmith/otf-api`
- Theme: Material with `navigation.instant`, `navigation.tabs`, `navigation.sections`, `content.code.copy`, `search.suggest`, `search.highlight`
- Plugin chain: `search`, `gen-files` (pointing to `tools/gen_ref_pages.py`), `literate-nav`, `autorefs`, `mkdocstrings`
- mkdocstrings Python handler config:
  - `paths: [src]`
  - `docstring_style: google`
  - `show_root_full_path: false`
  - `members_order: source`
  - `show_signature_annotations: true`
  - `filters: ["!^_", "!^model_"]`
  - `inherited_members: false`
  - `extensions: [griffe_pydantic: {schema: true}]`
- Markdown extensions: `admonition`, `pymdownx.details`, `pymdownx.superfences`, `pymdownx.highlight`, `pymdownx.inlinehilite`, `pymdownx.snippets`, `pymdownx.tabbed` (with `alternate_style: true`), `toc` (with `permalink: true`)
- `watch: [src/otf_api]`
- Nav structure (placeholder pages will be filled in later tasks):
  ```yaml
  nav:
    - Home: index.md
    - Getting Started: getting-started/index.md
    - Guides:
      - Authentication: guides/authentication.md
      - Bookings & Classes: guides/bookings.md
      - Workouts & Stats: guides/workouts.md
      - Studios: guides/studios.md
      - Challenges & Benchmarks: guides/challenges.md
      - Members: guides/members.md
      - Error Handling: guides/error-handling.md
    - Architecture: architecture/index.md
    - Troubleshooting: troubleshooting.md
    - Changelog: CHANGELOG.md
    - API Reference: reference/
  ```

### 2. Create `tools/gen_ref_pages.py`
Rewrite from hassette's `tools/gen_ref_pages.py` at `/home/jessica/source/hassette/tools/gen_ref_pages.py`. Use the allowlist approach with this `PUBLIC_MODULES` frozenset:
```python
PUBLIC_MODULES: frozenset[str] = frozenset({
    "otf_api.api.api",
    "otf_api.api.bookings.booking_api",
    "otf_api.api.members.member_api",
    "otf_api.api.studios.studio_api",
    "otf_api.api.workouts.workout_api",
    "otf_api.auth.user",
    "otf_api.models.bookings.bookings",
    "otf_api.models.bookings.bookings_v2",
    "otf_api.models.bookings.classes",
    "otf_api.models.bookings.enums",
    "otf_api.models.bookings.filters",
    "otf_api.models.members.member_detail",
    "otf_api.models.members.member_membership",
    "otf_api.models.members.member_purchases",
    "otf_api.models.members.notifications",
    "otf_api.models.studios.studio_detail",
    "otf_api.models.studios.studio_services",
    "otf_api.models.studios.enums",
    "otf_api.models.workouts.workout",
    "otf_api.models.workouts.performance_summary",
    "otf_api.models.workouts.telemetry",
    "otf_api.models.workouts.body_composition_list",
    "otf_api.models.workouts.challenge_tracker_content",
    "otf_api.models.workouts.challenge_tracker_detail",
    "otf_api.models.workouts.lifetime_stats",
    "otf_api.models.workouts.out_of_studio_workout_history",
    "otf_api.models.workouts.enums",
    "otf_api.exceptions",
    "otf_api.models.base",
    "otf_api.models.mixins",
})
```
Generate per-module `.md` files under `reference/` and a `reference/SUMMARY.md` for literate-nav. Delete the old `scripts/gen_ref_pages.py` (T08 should skip this deletion since it's already handled here).

### 3. Update `.readthedocs.yaml`
Change the `sphinx:` block to:
```yaml
mkdocs:
  configuration: mkdocs.yml
  fail_on_warning: true
```
Keep the existing `post_create_environment` and `post_install` jobs. Consider using hassette's approach (`python -m pip install --upgrade pip uv` instead of curl) for the uv install step.

### 4. Update `pyproject.toml` docs dependency group
Replace the current Sphinx dependencies with:
```toml
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

### 5. Create placeholder docs pages
Create minimal placeholder `.md` files for every page in the nav so `mkdocs build --strict` passes:
- `docs/index.md` — "# otf-api" with a one-liner
- `docs/getting-started/index.md` — "# Getting Started" placeholder
- `docs/guides/authentication.md`, `bookings.md`, `workouts.md`, `studios.md`, `challenges.md`, `members.md`, `error-handling.md` — title placeholders
- `docs/architecture/index.md` — placeholder
- `docs/troubleshooting.md` — placeholder
- `docs/CHANGELOG.md` — symlink to `../../CHANGELOG.md`

### 6. Create `docs/_static/custom.css`
Migrate the disclaimer footer styling from `source/_static/custom.css`. Add the disclaimer text via MkDocs-Material's `extra` config or custom CSS (check hassette for the pattern).

### 7. Verify locally
Run `uv sync --group docs` then `mkdocs build --strict` and `mkdocs serve`. Verify:
- API reference pages render for all `PUBLIC_MODULES`
- Pydantic model pages show field descriptions and hide `model_*` methods
- `exclude=True` fields are not visible
- Disclaimer footer appears on every page
- No build warnings or errors

## Focus
- The hassette `mkdocs.yml` is 164 lines — adapt it, don't start from scratch. Read it at `/home/jessica/source/hassette/mkdocs.yml`.
- hassette's `gen_ref_pages.py` is at `/home/jessica/source/hassette/tools/gen_ref_pages.py` (128 lines). It uses a tiered allowlist — adapt the pattern but use a flat frozenset since otf-api has fewer modules.
- The current `.readthedocs.yaml` uses `curl` to install uv. hassette uses `pip install uv` which is cleaner.
- Current pyproject.toml docs group is at line ~60-75 — search for `[dependency-groups]`.
- **Critical risk**: griffe-pydantic must handle `OtfItemBase` (custom base with `extra="ignore"`), `ApiMixin` (multiple inheritance), and `Field(exclude=True)`. Test these with `mkdocs serve` before considering this task done.
- The `tools/` directory may not exist yet — create it.

## Verify
- [ ] FR#1: `mkdocs build --strict` succeeds with no errors, producing a site with search, navigation tabs, and code syntax highlighting
- [ ] FR#2: API reference pages are auto-generated from docstrings — no hand-maintained reference stubs
- [ ] FR#3: At least one Pydantic model page (e.g., Booking, OtfClass) renders field names, types, defaults, and descriptions from `Field(description=...)`
- [ ] FR#4: `.readthedocs.yaml` is configured for MkDocs with `fail_on_warning: true`
- [ ] FR#13: Disclaimer footer appears on every rendered page
- [ ] AC#1: `mkdocs build --strict` produces a complete site with zero errors and zero warnings
- [ ] AC#3: Pydantic model pages hide `model_dump`, `model_validate`, etc. and do not show `exclude=True` fields
- [ ] AC#4: `.readthedocs.yaml` configured with `mkdocs:` block pointing to `mkdocs.yml`
- [ ] AC#9: Disclaimer footer renders on every page — verify on the landing page, a guide page, and the API reference
