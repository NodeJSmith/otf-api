---
task_id: "T08"
title: "Write troubleshooting page and remove Sphinx artifacts"
status: "planned"
depends_on: ["T01", "T02", "T03", "T04", "T05", "T06", "T07"]
implements: ["FR#9", "AC#8", "AC#10"]
---

## Summary
Write the troubleshooting page addressing known user pain points from GitHub issues, then delete all Sphinx artifacts (source/ directory, old gen_ref_pages.py, Sphinx dependencies). Also update README.md and CLAUDE.md references. This is the final task — only run after all MkDocs content is in place.

## Prompt

### 1. `docs/troubleshooting.md` — Troubleshooting
Source: GitHub issues (pain points already identified during design), `src/otf_api/exceptions.py`

Write a troubleshooting page covering these known issues:

**Pydantic validation errors**:
- Symptom: `ValidationError` on `get_workouts`, `get_performance_summaries`, or other data-fetching methods
- Cause: The upstream OTF API sometimes changes its response schema (adds/removes/renames fields). The library uses `extra="ignore"` to handle new fields gracefully, but type changes or removed required fields can still cause validation errors.
- Workaround: Update to the latest version of otf-api. If the issue persists, open a GitHub issue with the full traceback.

**Authentication failures**:
- Symptom: Login fails, token refresh fails, or "NoCredentialsError"
- Cause: Wrong credentials, expired cached tokens, or corrupted device key cache
- Solution: Verify `OTF_EMAIL` and `OTF_PASSWORD` are correct. Clear the cache: `from otf_api.cache import clear_cache; clear_cache()`. Try again.

**Workout count discrepancies**:
- Symptom: `get_workouts()` returns fewer workouts than the OTF app shows
- Cause: The API may not return all historical data, especially for older workouts or workouts from studios the user has since left
- Workaround: Use date range filtering to target specific periods. Note that the API is the source of truth, not the app's display.

**404 errors after version upgrades**:
- Symptom: `ResourceNotFoundError` or `404 Not Found` after upgrading otf-api
- Cause: The underlying OTF API endpoints change periodically. Newer library versions track these changes.
- Solution: Ensure you're on the latest version. Check the CHANGELOG for breaking changes.

**Environment variable reference**:
- `OTF_EMAIL` — OrangeTheory account email
- `OTF_PASSWORD` — OrangeTheory account password
- `OTF_LOG_LEVEL` — Logging level (default: INFO)

**Cache management**:
- Cache location and how to clear it
- When to clear the cache (auth issues, stale data)

### 2. Delete Sphinx artifacts
Remove the following files and directories:
- `source/` directory (all RST files, conf.py, _static/, _templates/)
- `scripts/gen_ref_pages.py` (replaced by `tools/gen_ref_pages.py` in T01)

### 3. Update project references
- **README.md**: Verify the documentation link (`https://otf-api.readthedocs.io/en/stable/`) is still correct. Update if the URL structure changed.
- **CLAUDE.md**: Update the "Common Commands" section — replace Sphinx commands with MkDocs equivalents:
  - `uv run mkdocs serve` (local dev server)
  - `uv run mkdocs build --strict` (build and verify)
  - Remove any references to `source/conf.py` or Sphinx

### 4. Final verification
Run `mkdocs build --strict` one last time to confirm the complete site builds cleanly with all content in place and no broken references to deleted Sphinx files.

## Focus
- The troubleshooting content is drawn from real GitHub issues — check the issues at `gh issue list --state all` if you need more context.
- Be careful with the Sphinx deletion — verify that no other files reference `source/conf.py` or the RST files before deleting.
- The README.md link to RTD docs should still work — ReadTheDocs preserves the URL structure across Sphinx→MkDocs migrations.
- CLAUDE.md is at the repo root — update it with the new doc build commands.
- This task depends on ALL prior tasks — don't run it until T01-T07 are complete.

## Verify
- [ ] FR#9: The troubleshooting page addresses Pydantic validation errors, auth failures, and workout count discrepancies
- [ ] AC#8: All three specific issues (validation errors, auth failures, workout count) are covered with symptoms, causes, and solutions
- [ ] AC#10: No Sphinx artifacts remain — `source/` directory is deleted, `scripts/gen_ref_pages.py` is deleted, no Sphinx packages in pyproject.toml deps
