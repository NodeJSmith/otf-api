"""Core anonymizer engine for the OTF API fixture anonymization pipeline.

Provides:
- ``AnonymizeConfig`` — configuration dataclass controlling strictness level and seed
- ``ReplacementMap`` — thread-safe dict that maintains referential integrity across calls
- ``Anonymizer`` — recursive JSON walker that applies PII field replacements
"""

import dataclasses
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import KNOWN_SAFE_FIELDS, FieldMapping

logger = logging.getLogger(__name__)

# Placeholder returned when a generator raises.  Must never equal a real PII value.
_GENERATOR_FAILURE_SENTINEL = "__ANONYMIZE_ERROR__"


# ---------------------------------------------------------------------------
# AnonymizeConfig
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class AnonymizeConfig:
    """Configuration for the Anonymizer engine.

    Attributes:
        seed: Optional integer seed for reproducible fake data generation.
        strictness: Controls how unknown fields (not in any FieldMapping) are handled:
            - "permissive": pass the value through unchanged
            - "mask": replace the value with the mask sentinel string
            - "drop": remove the key entirely from the output
        output_dir: Optional directory for fixture output files.  Defined here for
            forward-compatibility; consumed by WP05/WP06 (not used in this WP).
    """

    seed: int | None = None
    strictness: Literal["permissive", "mask", "drop"] = "permissive"
    output_dir: Path | None = None


# ---------------------------------------------------------------------------
# ReplacementMap
# ---------------------------------------------------------------------------

_UNKNOWN_FIELD_MASK = "__MASKED__"


class ReplacementMap:
    """Thread-safe mapping from real PII values to their fake replacements.

    Maintains referential integrity: the same real value always maps to the
    same fake value within a batch, regardless of how many times it appears.

    The map stores ``real_value → fake_value`` in-memory.  When serialized
    via ``to_json()`` / ``from_json()``, the ``real_value`` is the key (so
    round-trips work), but callers should treat this as an opaque format.
    """

    def __init__(self) -> None:
        self._map: dict[str, str] = {}
        self._lock = threading.Lock()

    def get_or_create(self, real_value: str, generator: Callable[[], str]) -> str:
        """Return the existing fake for *real_value*, or generate and store a new one.

        Args:
            real_value: The original PII value to look up or map.
            generator: Zero-argument callable that produces a fake replacement string.

        Returns:
            The fake replacement for *real_value* (consistent across calls).
        """
        with self._lock:
            if real_value in self._map:
                return self._map[real_value]
            fake = generator()
            self._map[real_value] = fake
            return fake

    def get_existing(self, real_value: str) -> str | None:
        """Return the existing fake for *real_value*, or None if not yet mapped."""
        with self._lock:
            return self._map.get(real_value)

    def to_json(self) -> dict[str, str]:
        """Return a serializable copy of the map (real → fake).

        Note: this includes real PII values as keys.  Callers should treat this
        as internal state and never expose the map to untrusted output.
        """
        with self._lock:
            return dict(self._map)

    @classmethod
    def from_json(cls, data: dict[str, str]) -> "ReplacementMap":
        """Restore a ReplacementMap from a previously serialized dict."""
        instance = cls()
        with instance._lock:
            instance._map.update(data)
        return instance


# ---------------------------------------------------------------------------
# Anonymizer
# ---------------------------------------------------------------------------


class Anonymizer:
    """Recursive JSON anonymizer.

    Walks a JSON-compatible dict, applies PII field replacements from the
    provided FieldMappings, and maintains a ReplacementMap for referential
    integrity across multiple calls.

    Args:
        config: Anonymization configuration.
        generators: Seeded fake data generators.
        mappings: List of FieldMapping entries describing how each PII field
            should be handled.
    """

    def __init__(
        self,
        config: AnonymizeConfig,
        generators: FakeDataGenerators,
        mappings: list[FieldMapping],
    ) -> None:
        self._config = config
        self._generators = generators
        self._mappings = mappings
        self._replacement_map = ReplacementMap()

        # Build an index: json_key → FieldMapping for O(1) lookup
        self._key_index: dict[str, FieldMapping] = {}
        for mapping in mappings:
            for key in mapping.json_keys:
                self._key_index[key] = mapping

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def anonymize_dict(self, data: dict[str, Any], context: str = "") -> dict[str, Any]:
        """Anonymize a JSON-compatible dict recursively.

        Args:
            data: The raw dict to anonymize.
            context: Optional endpoint path for logging/debugging.

        Returns:
            A new dict with PII fields replaced.
        """
        return self._walk_dict(data, context)

    def anonymize_value(self, key: str, value: Any) -> Any:  # noqa: ANN401
        """Apply the appropriate anonymization strategy for *key*/*value*.

        Rules:
        - If value is None: always return None (null preservation)
        - If key is in a FieldMapping: apply the mapping's strategy
        - Otherwise: apply the unknown-field policy from config.strictness

        Args:
            key: The JSON key name.
            value: The current value (may be any JSON-compatible type).

        Returns:
            The anonymized (or passed-through) value.
        """
        # Always preserve null values
        if value is None:
            return None

        mapping = self._key_index.get(key)
        if mapping is None:
            return self._handle_unknown_field(key, value)

        return self._apply_mapping(key, value, mapping)

    def anonymize_url(self, url: str) -> str:
        """Replace known PII values in a URL path and query string.

        Uses the current ReplacementMap to swap real values for their fakes.
        Only values already seen in prior ``anonymize_dict`` calls are replaced.

        Args:
            url: The URL string to anonymize.

        Returns:
            URL with known PII values replaced.
        """
        return self._substitute_from_map(url)

    def anonymize_filename(self, filename: str) -> str:
        """Replace known PII values in a fixture filename.

        Uses the current ReplacementMap to swap real values for their fakes.

        Args:
            filename: The filename string to anonymize.

        Returns:
            Filename with known PII values replaced.
        """
        return self._substitute_from_map(filename)

    # ------------------------------------------------------------------
    # Internal: recursive walk helpers
    # ------------------------------------------------------------------

    def _walk_dict(self, data: dict[str, Any], context: str) -> dict[str, Any]:
        """Recursively walk a dict, returning a new dict with PII replaced."""
        result: dict[str, Any] = {}
        for key, value in data.items():
            # Check if this key is a known PII field
            if key in self._key_index:
                anonymized = self.anonymize_value(key, value)
                result[key] = anonymized
            elif key in KNOWN_SAFE_FIELDS:
                # Known safe fields: always pass through without recursion check
                result[key] = value
            elif isinstance(value, dict):
                # Unknown key but dict value: recurse
                result[key] = self._walk_dict(value, context)
            elif isinstance(value, list):
                # Unknown key but list value: recurse
                result[key] = self._walk_list(value, context)
            else:
                if self._config.strictness == "drop":
                    continue
                result[key] = self.anonymize_value(key, value)
        return result

    def _walk_list(self, items: list[Any], context: str) -> list[Any]:
        """Recursively walk a list, processing any dict/list elements."""
        result: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                result.append(self._walk_dict(item, context))
            elif isinstance(item, list):
                result.append(self._walk_list(item, context))
            else:
                result.append(item)
        return result

    # ------------------------------------------------------------------
    # Internal: strategy dispatch
    # ------------------------------------------------------------------

    def _apply_mapping(self, key: str, value: Any, mapping: FieldMapping) -> Any:  # noqa: ANN401
        """Apply the FieldMapping strategy to *value*, with referential integrity if needed."""
        category = mapping.category

        if mapping.referential:
            # For referential fields, convert to string for map keying
            real_str = str(value)
            return self._replacement_map.get_or_create(
                real_str,
                lambda: self._generate_for_category(category, key, value),
            )
        return self._generate_for_category(category, key, value)

    def _generate_for_category(self, category: str, key: str, value: Any) -> Any:  # noqa: ANN401
        """Dispatch to the correct generator method for a given category.

        If the generator raises, returns a deterministic placeholder instead of
        the real value (design doc edge case 12: never pass through real PII on
        generator failure).
        """
        try:
            return self._call_generator(category, key, value)
        except Exception:
            logger.warning(
                "Generator failed for key=%r category=%r; using fallback placeholder",
                key,
                category,
                exc_info=True,
            )
            # Deterministic placeholder — includes key for debuggability
            return f"{_GENERATOR_FAILURE_SENTINEL}[{key}]"

    def _call_generator(self, category: str, key: str, value: Any) -> Any:  # noqa: ANN401
        """Call the appropriate FakeDataGenerators method for *category*."""
        g = self._generators

        if category == "identity_uuid":
            return g.fake_uuid()
        if category == "identity_numeric":
            return g.fake_numeric_id()
        if category == "name":
            return g.fake_name()
        if category == "email":
            return g.fake_email()
        if category == "phone":
            return g.fake_phone()
        if category == "address":
            # Address strategy returns a dict of components; return the specific key's value
            components = g.fake_address_components()
            # Return the specific field from the components dict, or a generic fake city
            return components.get(key, components.get("city", "FakeCity"))
        if category == "birthday":
            return g.fake_birthday()
        if category == "financial_cc_last4":
            return g.fake_cc_last4()
        if category == "financial_cc_type":
            return g.fake_cc_type()
        if category == "financial_price":
            return g.fake_price()
        if category == "gender":
            return g.fake_gender()
        if category == "biometric_scalar":
            orig = float(value) if value is not None else 0.0
            return g.fake_biometric_scalar(key, orig)
        if category == "biometric_body_comp":
            orig = float(value) if value is not None else 0.0
            return round(orig * g.fake_body_comp_factor(), 4)
        if category == "biometric_telemetry":
            orig = int(value) if value is not None else 0
            return orig + g.fake_hr_delta()
        if category == "auth_token":
            return "REDACTED"
        if category == "image_url":
            return g.fake_image_url()
        if category == "timestamp":
            # Return a placeholder timestamp string — full offset logic in WP03
            return str(value)
        logger.warning("Unknown category %r for key=%r; returning original", category, key)
        return value

    def _handle_unknown_field(self, _key: str, value: Any) -> Any:  # noqa: ANN401
        """Handle a field that is not in any FieldMapping per config.strictness."""
        strictness = self._config.strictness
        if strictness == "permissive":
            return value
        if strictness == "mask":
            return _UNKNOWN_FIELD_MASK
        # "drop" — caller (_walk_dict) handles removal; return mask as fallback
        return _UNKNOWN_FIELD_MASK

    # ------------------------------------------------------------------
    # Internal: string substitution from replacement map
    # ------------------------------------------------------------------

    def _substitute_from_map(self, text: str) -> str:
        """Replace all known real→fake mappings in *text*.

        Iterates over all current replacement map entries and performs
        substring replacement.
        """
        current_map = self._replacement_map.to_json()
        result = text
        for real_value, fake_value in current_map.items():
            if real_value in result:
                result = result.replace(real_value, str(fake_value))
        return result
