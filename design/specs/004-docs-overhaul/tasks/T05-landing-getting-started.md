---
task_id: "T05"
title: "Write landing page and getting started guide"
status: "planned"
depends_on: ["T01"]
implements: ["FR#5", "FR#12", "AC#5", "AC#13"]
---

## Summary
Write the documentation landing page (`docs/index.md`) and the getting started guide (`docs/getting-started/index.md`). The landing page is the first thing users see — it must clearly communicate what the library does, how to install it, and where to go next. The getting started guide is the zero-to-API-call walkthrough that lets a new user make their first successful API call.

## Prompt
Replace the placeholder pages created in T01 with full content.

### 1. `docs/index.md` — Landing page
Write a landing page that includes:
- **Title and tagline**: "otf-api" with a one-line description ("Python client for the OrangeTheory Fitness API")
- **What it does**: 2-3 sentences explaining the library's purpose — typed API clients for bookings, workouts, studios, and member data, built on Pydantic v2 and httpx
- **Installation**: `pip install otf-api` code block
- **Quick example**: A minimal code snippet showing initialization and one API call (e.g., getting upcoming classes). Keep it to ~10 lines.
- **Feature highlights**: Brief bullet list of key capabilities (class booking, workout history, studio search, challenge tracking, automatic token caching)
- **Navigation links**: Point to Getting Started, Guides, API Reference, and Troubleshooting

Use the current `source/index.rst` content as a starting point but expand significantly. Reference hassette's `docs/index.md` at `/home/jessica/source/hassette/docs/index.md` for structure and tone.

### 2. `docs/getting-started/index.md` — Getting started guide
Write a step-by-step walkthrough covering:

**Prerequisites**: Python 3.11+, an active OrangeTheory Fitness membership

**Installation**: `pip install otf-api` (and optionally `uv add otf-api`)

**Authentication setup**: Three methods:
1. Environment variables: `OTF_EMAIL` and `OTF_PASSWORD`
2. Direct credentials: `Otf(user=OtfUser(email="...", password="..."))`
3. `OtfUser` with prompt: `Otf(user=OtfUser())` (prompts for credentials)

Explain that the library caches authentication tokens to disk via `diskcache`, so subsequent runs don't re-authenticate.

**First API call**: Show a complete working example:
```python
from otf_api import Otf

otf = Otf()
# Get your member info
print(otf.member.first_name, otf.member.last_name)

# Get your home studio
print(otf.home_studio.name)
```

**Next steps**: Link to the domain guides (bookings, workouts, studios) and the API reference.

Read the current `source/index.rst` and `src/otf_api/api/api.py` (the `Otf.__init__` docstring) for accurate initialization details. Read `src/otf_api/auth/user.py` for `OtfUser` initialization patterns.

## Focus
- The current `source/index.rst` at `source/index.rst` has a basic code example — expand it, don't just copy it.
- `OtfUser` initialization is documented in `src/otf_api/auth/user.py` — read the `__init__` docstring for the three credential patterns.
- The `Otf` class auto-creates an `OtfUser` from env vars if no user is passed — document this default behavior.
- Token caching uses `diskcache` — the cache directory is platform-specific. Mention that tokens are cached but don't go deep (that's for the auth guide).
- Code examples must be accurate — verify method names and signatures against the actual source.
- Don't mention the anonymizer or OpenAPI schema generation on the landing page — those are developer utilities, not the primary use case.

## Verify
- [ ] FR#5: The getting started guide includes installation, credential setup (all three methods), and a first API call example
- [ ] FR#12: The landing page has a description, installation command, feature list, and links to all major sections
- [ ] AC#5: Following only the getting started guide, a user would know how to install, set credentials, and call `otf.member`
- [ ] AC#13: The landing page contains an installation command, description, and links to getting started, guides, and API reference
