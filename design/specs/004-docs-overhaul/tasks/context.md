# Context: Documentation Overhaul — Sphinx to MkDocs-Material

## Problem & Motivation
The otf-api library's documentation is sparse and fragmented. Users open GitHub issues asking basic questions (Pydantic validation errors, auth setup, workout count mismatches) because there are no guides to answer them. The current site has a single landing page with one code snippet, four raw Python file renders, and auto-generated API stubs. Contributors must read source code to understand the four-domain architecture. The Sphinx/RST tooling adds friction — Markdown is easier to write and maintain. The hassette project (same author) has a proven MkDocs-Material setup that serves as the template for this migration.

## Visual Artifacts
None.

## Key Decisions
1. **MkDocs-Material over Sphinx/Furo** — Markdown is lower friction for guide writing, Material theme has better navigation/search UX, and griffe's AST parsing avoids import side effects from the package's `__init__.py` logging setup.
2. **griffe-pydantic for Pydantic model rendering** — replaces the 30-entry `PYDANTIC_IGNORE_FIELDS` exclusion list in Sphinx's conf.py with template-level rendering that shows `Field(description=...)` values as structured field documentation.
3. **Allowlist-based gen_ref_pages.py** — follows hassette's pattern of explicitly listing public modules rather than a skiplist approach, preventing internal modules from leaking into the API reference.
4. **ReadTheDocs webhook deployment** — keep the existing RTD integration, just swap the config from `sphinx:` to `mkdocs:`.
5. **Exception classes exported in `__all__`** — users need `from otf_api.exceptions import ConflictingBookingError` to catch specific errors.
6. **Delete Sphinx artifacts last** — only after MkDocs site is verified, to avoid a broken docs gap.

## Constraints & Anti-Patterns
- Do NOT use Sphinx or RST — no hybrid approach
- Do NOT trigger package imports during doc builds (use AST parsing via griffe, not runtime import)
- Do NOT document `*_client.py` files — internal HTTP transport
- Do NOT include `anonymize/` sub-package in user-facing guides
- Do NOT create versioned docs or a contributor guide (explicit non-goals)
- Do NOT add `from __future__ import annotations` to any file
- Model the docs structure after hassette at `/home/jessica/source/hassette`
- Test griffe-pydantic rendering locally with `mkdocs serve` before committing to guide writing

## Design Doc References
- `## Problem` — three compounding issues: self-service, friction, credibility
- `## Architecture` — tooling stack table, config file specs, docs directory structure, Pydantic rendering strategy, source code changes, files to delete
- `## Edge Cases` — excluded fields, multiple inheritance, dual booking APIs, import side effects, computed fields, alias fields
- `## Key Constraints` — five explicit prohibitions
- `## Dependencies and Assumptions` — griffe-pydantic validation assumption
- `## Test Strategy` — six verification approaches
