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
from urllib.parse import quote

from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import KNOWN_SAFE_FIELDS, FieldMapping

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain detection constants
# ---------------------------------------------------------------------------

# Minimum set of fields that must ALL be present to classify a dict as a body
# composition scan.  Checking for three distinct fields avoids false positives
# from dicts that happen to contain a single body-comp key.
_BODY_COMP_DETECTION_KEYS: frozenset[str] = frozenset({"tbw", "bfm", "lbm"})

# Identifier keys searched (in order) when correlating address fields to a
# parent location.  The first one found in the current dict is used.
_ADDRESS_IDENTIFIER_KEYS: tuple[str, ...] = (
    "studioUUId",
    "studio_uuid",
    "memberAddressUUId",
)

# OTF heart-rate zone boundary percentages of maxHr.  Ordered from lowest to
# highest so zone recalculation can iterate in a stable sequence.
_OTF_ZONE_PERCENTAGES: dict[str, tuple[float, float]] = {
    "gray": (0.0, 0.62),
    "blue": (0.62, 0.72),
    "green": (0.72, 0.84),
    "orange": (0.84, 0.92),
    "red": (0.92, 1.0),
}

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

        Empty strings are never stored in the map — they are returned as-is
        to avoid substring substitution explosions in anonymize_url/anonymize_filename.

        Args:
            real_value: The original PII value to look up or map.
            generator: Zero-argument callable that produces a fake replacement string.

        Returns:
            The fake replacement for *real_value* (consistent across calls).
        """
        # Never map empty strings — would cause infinite substitution loops
        if not real_value:
            return generator()

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

        # Per-location address component cache.
        # Key: location identifier string (e.g. studioUUId value)
        # Value: dict of fake address components from fake_address_components()
        self._address_component_cache: dict[str, dict[str, str]] = {}
        self._address_cache_lock = threading.Lock()

    @property
    def replacement_map(self) -> ReplacementMap:
        """The underlying ReplacementMap for this anonymizer instance."""
        return self._replacement_map

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
        """Recursively walk a dict, returning a new dict with PII replaced.

        Before the per-field loop, domain-specific structure detection runs:

        1. Body composition scan — detected by presence of ``tbw``, ``bfm``,
           and ``lbm`` keys.  One scale factor is generated and applied
           uniformly to all body-comp fields in this dict.
        2. Workout with telemetry — detected by ``maxHr`` plus a ``zones``
           sub-dict.  Zone BPM boundaries are recalculated from the anonymized
           ``maxHr`` *after* per-field processing.
        3. Address correlation — when address fields are present alongside a
           known location identifier key (e.g. ``studioUUId``), all address
           fields in this dict are correlated to one fake address via the
           replacement map.
        """
        dict_keys = set(data.keys())

        # ------------------------------------------------------------------
        # Domain detection: body composition scan
        # ------------------------------------------------------------------
        if dict_keys >= _BODY_COMP_DETECTION_KEYS:
            return self._anonymize_body_comp_scan(data, context)

        # ------------------------------------------------------------------
        # Domain detection: address correlation
        # ------------------------------------------------------------------
        # Find the location identifier for this dict, if any.
        location_id: str | None = None
        for id_key in _ADDRESS_IDENTIFIER_KEYS:
            if id_key in data and data[id_key] is not None:
                location_id = str(data[id_key])
                break

        # ------------------------------------------------------------------
        # Per-field walk
        # ------------------------------------------------------------------
        result: dict[str, Any] = {}
        for key, value in data.items():
            # Check if this key is a known PII field
            if key in self._key_index:
                mapping = self._key_index[key]
                if mapping.category == "address" and location_id is not None:
                    anonymized = self._anonymize_address_with_correlation(key, value, location_id)
                else:
                    anonymized = self.anonymize_value(key, value)
                result[key] = anonymized
            elif key in KNOWN_SAFE_FIELDS:
                # Known safe fields: always pass through without recursion check
                result[key] = value
            elif isinstance(value, dict):
                # Unknown key but dict value: recurse
                result[key] = self._walk_dict(value, context)
            elif isinstance(value, list):
                # Unknown key but list value: check for telemetry structure
                if self._is_telemetry_list(value):
                    result[key] = self._anonymize_telemetry_list(value)
                else:
                    result[key] = self._walk_list(value, context)
            else:
                if self._config.strictness == "drop":
                    continue
                result[key] = self.anonymize_value(key, value)

        # ------------------------------------------------------------------
        # Domain detection: zone recalculation (post-walk)
        #
        # After per-field processing, if this dict had both maxHr (now
        # anonymized) and a zones sub-dict, recalculate zone BPM boundaries
        # from the new maxHr value.
        # ------------------------------------------------------------------
        if "maxHr" in result and "zones" in result and isinstance(result["zones"], dict):
            result["zones"] = self._recalculate_zones(result["maxHr"], result["zones"])

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
    # Internal: domain-specific transforms
    # ------------------------------------------------------------------

    def _anonymize_body_comp_scan(self, data: dict[str, Any], context: str) -> dict[str, Any]:
        """Anonymize a body composition scan dict.

        Generates one scale factor for the entire scan and applies it uniformly
        to every ``biometric_body_comp`` field, preserving the mathematical
        relationships between mass components (lean mass + fat mass ≈ total).

        ``bmi`` and ``pbf`` are derived fields that must be *recalculated*
        rather than scaled:

        - ``bmi`` = weight_kg / height_m²  (weight in kg, height in m)
        - ``pbf`` = (bfm / (bfm + lbm)) * 100

        Because weight and height are in the ``biometric_scalar`` category
        (not body_comp), and may not be present in every scan dict, we scale
        ``bmi`` and ``pbf`` using the same factor as other body comp fields
        rather than attempting a full recalculation from absent fields.
        This preserves the ratio while keeping the value realistic.
        """
        factor = self._generators.fake_body_comp_factor()

        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in self._key_index and self._key_index[key].category == "biometric_body_comp":
                if value is None:
                    result[key] = None
                else:
                    result[key] = round(float(value) * factor, 4)
            elif key in self._key_index:
                result[key] = self.anonymize_value(key, value)
            elif key in KNOWN_SAFE_FIELDS:
                result[key] = value
            elif isinstance(value, dict):
                result[key] = self._walk_dict(value, context)
            elif isinstance(value, list):
                result[key] = self._walk_list(value, context)
            else:
                if self._config.strictness == "drop":
                    continue
                result[key] = self.anonymize_value(key, value)
        return result

    @staticmethod
    def _is_telemetry_list(items: list[Any]) -> bool:
        """Return True if *items* looks like an HR telemetry array.

        Detection requires the list to be non-empty and the first element to
        be a dict containing both ``hr`` and ``relativeTimestamp`` keys.
        """
        if not items:
            return False
        first = items[0]
        if not isinstance(first, dict):
            return False
        return "hr" in first and "relativeTimestamp" in first

    def _anonymize_telemetry_list(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anonymize a telemetry array with a single consistent HR delta.

        Generates one ``hr_delta`` for the entire array so relative HR
        profiles are preserved (consistent offset across all HR samples).
        """
        delta = self._generators.fake_hr_delta()
        result: list[dict[str, Any]] = []
        for item in items:
            anon_item = dict(item)
            if "hr" in anon_item and anon_item["hr"] is not None:
                anon_item["hr"] = int(anon_item["hr"]) + delta
            result.append(anon_item)
        return result

    def _recalculate_zones(self, anon_max_hr: Any, zones: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN401
        """Recalculate heart-rate zone boundaries from the anonymized maxHr.

        OTF zones are defined as fixed percentages of maxHr.  After maxHr is
        anonymized, zone BPM boundaries must be recalculated from the *new*
        value so they remain internally consistent.

        Only zones whose names match the known OTF zone names are recalculated.
        Unknown zone names are passed through unchanged.

        If *anon_max_hr* is not a numeric type (e.g. the generator produced a
        sentinel string), zone data is passed through unchanged.
        """
        # Guard against generator-failure sentinels or unexpected types
        try:
            max_hr_float = float(anon_max_hr)
        except (TypeError, ValueError):
            logger.debug("Cannot recalculate zones: maxHr=%r is not numeric", anon_max_hr)
            return dict(zones)

        result: dict[str, Any] = {}
        for zone_name, zone_data in zones.items():
            if zone_name not in _OTF_ZONE_PERCENTAGES or not isinstance(zone_data, dict):
                result[zone_name] = zone_data
                continue
            lo_pct, hi_pct = _OTF_ZONE_PERCENTAGES[zone_name]
            new_zone = dict(zone_data)
            if "startBpm" in new_zone:
                new_zone["startBpm"] = round(max_hr_float * lo_pct)
            if "endBpm" in new_zone:
                new_zone["endBpm"] = round(max_hr_float * hi_pct)
            result[zone_name] = new_zone
        return result

    def _anonymize_address_with_correlation(self, key: str, value: Any, location_id: str) -> Any:  # noqa: ANN401
        """Anonymize an address field correlated to a location identifier.

        All address fields within the same location (identified by ``location_id``)
        share one generated set of fake address components.  This ensures that
        ``address1``, ``city``, ``state``, and ``postalCode`` for the same
        studio produce a self-consistent fake address, regardless of the original
        string values.

        The ``_address_component_cache`` (keyed by location_id) stores the
        generated component dict so subsequent fields in the same dict —
        and subsequent ``anonymize_dict`` calls with the same location_id —
        all reuse the same fake address.
        """
        if value is None:
            return None

        with self._address_cache_lock:
            if location_id not in self._address_component_cache:
                self._address_component_cache[location_id] = self._generators.fake_address_components()
            components = self._address_component_cache[location_id]

        return components.get(key, components.get("city", "FakeCity"))

    # ------------------------------------------------------------------
    # Internal: strategy dispatch
    # ------------------------------------------------------------------

    def _apply_mapping(self, key: str, value: Any, mapping: FieldMapping) -> Any:  # noqa: ANN401
        """Apply the FieldMapping strategy to *value*, with referential integrity if needed."""
        category = mapping.category

        if mapping.referential:
            # For referential fields, convert to string for map keying
            real_str = str(value)
            fake = self._replacement_map.get_or_create(
                real_str,
                lambda: self._generate_for_category(category, key, value),
            )
            # Coerce the fake value to match the original value's type.
            # The replacement map may have been seeded by a different key with
            # the same numeric ID but a different Python type (e.g. int vs str).
            if category == "identity_numeric" and isinstance(value, str) and not isinstance(fake, str):
                return str(fake)
            return fake
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
            fake_id = g.fake_numeric_id()
            # Preserve the original type: if the real value was a string, return a string
            if isinstance(value, str):
                return str(fake_id)
            return fake_id
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
            fake_price = g.fake_price()
            # Preserve original type: some models store price as str
            if isinstance(value, str):
                return str(fake_price)
            return fake_price
        if category == "gender":
            return g.fake_gender()
        if category == "biometric_scalar":
            try:
                orig = float(value) if value is not None else 0.0
            except (TypeError, ValueError):
                orig = 0.0
            fake_scalar = g.fake_biometric_scalar(key, orig)
            # Preserve original type: models may expect int or str for biometric fields
            if isinstance(value, int) and not isinstance(value, bool):
                return round(fake_scalar)
            if isinstance(value, str):
                return str(round(fake_scalar))
            return fake_scalar
        if category == "biometric_body_comp":
            try:
                orig = float(value) if value is not None else 0.0
            except (TypeError, ValueError):
                orig = 0.0
            return round(orig * g.fake_body_comp_factor(), 4)
        if category == "biometric_telemetry":
            try:
                orig = int(value) if value is not None else 0
            except (TypeError, ValueError):
                orig = 0
            return orig + g.fake_hr_delta()
        if category == "auth_token":
            return "REDACTED"
        if category == "image_url":
            return g.fake_image_url()
        if category == "timestamp":
            # Timestamps are passed through unchanged; offset logic is deferred.
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

    # Minimum key length for filename/URL substitution.  Short keys (e.g. single
    # digits like '5', '6') appear as substrings of UUIDs, timestamps, and other
    # safe identifiers, so substituting them in filenames would corrupt the path.
    # 8 chars is sufficient to be unambiguous in URL/filename context; full UUIDs
    # (36 chars) are the primary target.
    _MIN_SUBSTITUTE_LEN: int = 8

    def _substitute_from_map(self, text: str) -> str:
        """Replace all known real→fake mappings in *text*.

        Iterates over all current replacement map entries and performs
        substring replacement.  Also substitutes URL-encoded forms of each
        real value so that filenames containing percent-encoded PII (e.g.
        ``email=foo%40bar.com``) are correctly anonymized.

        Empty-string keys and short keys (< 8 chars) are skipped to prevent
        substitution explosions in filenames/URLs.
        """
        current_map = self._replacement_map.to_json()
        result = text
        # Sort by key length descending so longer (more specific) patterns are
        # replaced before shorter ones, avoiding partial double-replacement.
        for real_value, fake_value in sorted(current_map.items(), key=lambda kv: -len(kv[0])):
            # Skip empty-string keys — replacing "" inserts the fake value
            # between every single character.
            if not real_value:
                continue
            # Skip short keys — they match too broadly in filenames/URLs and
            # would corrupt UUID strings already written into the path.
            if len(real_value) < self._MIN_SUBSTITUTE_LEN:
                continue
            if real_value in result:
                result = result.replace(real_value, str(fake_value))
            # Also handle URL-encoded form (e.g. "@" → "%40" in email addresses
            # embedded in query-string filenames).
            url_encoded = quote(real_value, safe="")
            if url_encoded != real_value and url_encoded in result:
                result = result.replace(url_encoded, quote(str(fake_value), safe=""))
        return result
