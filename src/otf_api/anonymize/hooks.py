"""Real-time capture hook for the OTF API anonymization pipeline.

Provides:
- ``AnonymizedCaptureHook`` — httpx response event hook that anonymizes and
  writes each API response to the debug output directory.
- ``create_capture_hook`` — factory that reads configuration from environment
  variables and constructs a ready-to-use hook instance.
"""

import datetime
import json
import logging
import os
import re
from pathlib import Path

import httpx
import platformdirs

from otf_api.anonymize._io import atomic_write as _atomic_write
from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer
from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import FIELD_MAPPINGS

logger = logging.getLogger(__name__)

# Default output directory for captured responses.
_DEFAULT_OUTPUT_DIR = Path(platformdirs.user_cache_dir("otf-api")) / "debug"


def _slugify_path(path: str) -> str:
    """Convert a URL path to a safe filename slug.

    Replaces slashes and other special characters with underscores.

    Args:
        path: The URL path to slugify.

    Returns:
        A filename-safe string derived from the path.
    """
    # Strip leading slash
    slug = path.lstrip("/")
    # Replace path separators and non-alphanumeric chars with underscores
    slug = re.sub(r"[^a-zA-Z0-9._-]", "_", slug)
    # Collapse multiple underscores
    slug = re.sub(r"_+", "_", slug)
    # Strip trailing underscores
    slug = slug.strip("_")
    return slug or "root"


class AnonymizedCaptureHook:
    """httpx response event hook that captures and anonymizes API responses.

    Designed to be injected into ``httpx.Client.event_hooks["response"]`` at
    session initialization.  The hook is session-scoped: it reuses a single
    ``Anonymizer`` instance across all requests, preserving referential
    integrity across multiple responses (the same UUID always maps to the same
    fake UUID for the lifetime of the session).

    The hook is purely observational — it never modifies the actual
    ``httpx.Response`` object.  Any error inside the hook is caught and logged
    so that a broken anonymizer never breaks the library.

    Args:
        anonymizer: The anonymizer instance to use for all captures.
        output_dir: Directory where captured files are written.
    """

    def __init__(self, anonymizer: Anonymizer, output_dir: Path) -> None:
        self._anonymizer = anonymizer
        self._output_dir = output_dir
        self._first_call_done = False
        self._seen_slugs: dict[str, int] = {}

    @property
    def anonymizer(self) -> Anonymizer:
        """The underlying Anonymizer instance (for tests / introspection)."""
        return self._anonymizer

    @property
    def output_dir(self) -> Path:
        """The output directory for captured files."""
        return self._output_dir

    def __call__(self, response: httpx.Response) -> None:
        """Handle a completed httpx response.

        Reads the response body, anonymizes it, and writes it to the output
        directory.  Non-JSON responses are skipped with a warning.  Any error
        is logged without re-raising so that the library is never broken by a
        capture failure.

        Args:
            response: The completed httpx.Response (not modified by this hook).
        """
        try:
            self._handle_response(response)
        except Exception:
            logger.warning(
                "AnonymizedCaptureHook: unexpected error capturing %s %s — skipping",
                response.request.method,
                response.request.url,
                exc_info=True,
            )

    def _handle_response(self, response: httpx.Response) -> None:
        """Internal response handler (may raise; caller catches)."""
        if not self._first_call_done:
            self._write_capture_start()
            self._first_call_done = True

        response.read()

        if response.status_code >= 400:
            logger.debug(
                "AnonymizedCaptureHook: skipping %d response from %s %s",
                response.status_code,
                response.request.method,
                response.request.url,
            )
            return

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type and "json" not in content_type:
            # Try to parse as JSON anyway (some APIs omit or misset content-type)
            try:
                raw_json = response.json()
            except Exception:
                logger.warning(
                    "AnonymizedCaptureHook: non-JSON response from %s %s (content-type=%r) — skipping",
                    response.request.method,
                    response.request.url,
                    content_type,
                )
                return
        else:
            try:
                raw_json = response.json()
            except Exception:
                logger.warning(
                    "AnonymizedCaptureHook: failed to parse JSON from %s %s — skipping",
                    response.request.method,
                    response.request.url,
                    exc_info=True,
                )
                return

        url = response.request.url
        host = url.host
        path = str(url.path)

        # Anonymize the JSON body
        if isinstance(raw_json, dict):
            anonymized_body = self._anonymizer.anonymize_dict(raw_json, context=path)
        elif isinstance(raw_json, list):
            anonymized_body = self._anonymizer.anonymize_list(raw_json, context=path)
        else:
            anonymized_body = raw_json

        # Anonymize the URL (replaces any PII already seen in the body)
        anonymized_url = self._anonymizer.anonymize_url(str(url))

        # Build output path: output_dir/<host>/<slugified-path>.json
        # Include query params in the slug to differentiate same-path requests.
        # Anonymize the slug AFTER body processing so the replacement map
        # already contains any UUIDs found in the response body.
        query = str(url.params) if url.params else ""
        raw_slug = _slugify_path(path)
        if query:
            raw_slug = f"{raw_slug}___{_slugify_path(query)}"
        slug = self._anonymizer.anonymize_filename(raw_slug)

        # Collision counter: append ___N for repeated slugs
        slug_key = slug
        count = self._seen_slugs.get(slug_key, 0) + 1
        self._seen_slugs[slug_key] = count
        if count > 1:
            slug = f"{slug}___{count}"

        host_dir = self._output_dir / host
        host_dir.mkdir(parents=True, exist_ok=True)
        output_file = host_dir / f"{slug}.json"

        payload = {
            "url": anonymized_url,
            "method": response.request.method,
            "status_code": response.status_code,
            "body": anonymized_body,
        }

        _atomic_write(output_file, json.dumps(payload, indent=2, default=str))
        logger.debug("AnonymizedCaptureHook: wrote capture to %s", output_file)

    def _write_capture_start(self) -> None:
        """Write a _capture_start.json sentinel to the output directory."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        sentinel_path = self._output_dir / "_capture_start.json"
        payload = {
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "output_dir": str(self._output_dir),
            "strictness": self._anonymizer.config.strictness,
            "seed": self._anonymizer.config.seed,
        }
        _atomic_write(sentinel_path, json.dumps(payload, indent=2))
        logger.debug("AnonymizedCaptureHook: wrote capture start sentinel to %s", sentinel_path)


def create_capture_hook(config: AnonymizeConfig | None = None) -> AnonymizedCaptureHook:
    """Factory that builds an ``AnonymizedCaptureHook`` from environment variables.

    Environment variables:
        OTF_ANONYMIZE_RESPONSES: Set to ``true`` to enable capture (default: disabled).
            This factory is called only when capture is enabled — the check lives
            in the caller.
        OTF_ANONYMIZE_OUTPUT_DIR: Override the output directory.
            Default: ``platformdirs.user_cache_dir("otf-api") / "debug"``.
        OTF_ANONYMIZE_SEED: Override the integer seed for fake data generation.
            Default: derived from the member UUID (handled by the caller).
        OTF_ANONYMIZE_STRICTNESS: One of ``permissive``, ``mask``, or ``drop``.
            Default: ``mask``.

    Args:
        config: Optional pre-built ``AnonymizeConfig``.  If provided, env vars
            are not consulted (useful for programmatic configuration in tests).

    Returns:
        A fully initialised ``AnonymizedCaptureHook`` ready for injection.
    """
    if config is None:
        # --- output_dir ---
        output_dir_env = os.getenv("OTF_ANONYMIZE_OUTPUT_DIR")
        output_dir = Path(output_dir_env) if output_dir_env else _DEFAULT_OUTPUT_DIR

        # --- seed ---
        seed_env = os.getenv("OTF_ANONYMIZE_SEED")
        seed: int | None = None
        if seed_env is not None:
            try:
                seed = int(seed_env)
            except ValueError:
                logger.warning(
                    "AnonymizedCaptureHook: OTF_ANONYMIZE_SEED=%r is not a valid integer; using random seed",
                    seed_env,
                )

        # --- strictness ---
        strictness_raw = os.getenv("OTF_ANONYMIZE_STRICTNESS", "mask").lower()
        if strictness_raw not in ("permissive", "mask", "drop"):
            logger.warning(
                "AnonymizedCaptureHook: OTF_ANONYMIZE_STRICTNESS=%r is invalid; defaulting to 'mask'",
                strictness_raw,
            )
            strictness_raw = "mask"

        config = AnonymizeConfig(
            seed=seed,
            strictness=strictness_raw,  # type: ignore[arg-type]
            output_dir=output_dir,
        )
    else:
        output_dir = config.output_dir or _DEFAULT_OUTPUT_DIR

    generators = FakeDataGenerators(seed=config.seed)
    anonymizer = Anonymizer(config=config, generators=generators, mappings=FIELD_MAPPINGS)

    return AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=output_dir)
