"""Post-anonymization validator for the OTF API fixture anonymization pipeline.

Checks that anonymized output:
1. Contains no leaked real PII values (case-insensitive, including URL-encoded variants)
2. Preserves JSON structural integrity (same keys, same types, same nesting, nulls preserved)
3. Can be parsed through the corresponding Pydantic model

Public API:
    - ``ValidationResult`` — dataclass summarising one validation run
    - ``LeakReport`` — dataclass describing one detected leak
    - ``PiiValidator`` — the validator class
    - ``collect_real_values`` — helper to extract PII values from a raw dict
"""

import dataclasses
import importlib
import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from otf_api.anonymize.mappings import FieldMapping

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class LeakReport:
    """Describes a single PII leak found in the anonymized output.

    Attributes:
        file: Filename of the fixture where the leak was found.
        field_path: Dot-separated path to the field containing the leak (e.g. "data.firstName").
        real_value: The real PII value that was found in the output.
        category: The PII category this value belongs to (e.g. "name", "email").
    """

    file: str
    field_path: str
    real_value: str
    category: str


@dataclasses.dataclass
class ValidationResult:
    """Summarises the result of validating one or more anonymized fixtures.

    Attributes:
        passed: True iff there are no leaks, structural errors, or model parse errors.
        leaks: List of detected PII leaks.
        structural_errors: List of structural integrity error messages.
        model_parse_errors: List of model parsing error messages (best-effort).
    """

    passed: bool
    leaks: list[LeakReport]
    structural_errors: list[str]
    model_parse_errors: list[str]


# ---------------------------------------------------------------------------
# Endpoint-to-model mapping
# ---------------------------------------------------------------------------
# Maps regex patterns that match fixture filenames/paths to Pydantic model
# import paths and any extraction hint needed to locate the data in the fixture.
#
# Format:
#   (pattern, model_class_path, extraction_key_or_None)
#
# extraction_key: if the fixture has a wrapper (e.g. "data" or "items"), this
#   is the key to extract the payload. "data" → fixture["data"]
#   "Dto" → fixture["Dto"]
#   None → use the entire fixture dict
#   "items[0]" → first item from fixture["items"]
#
# Model import paths are resolved lazily so that importing this module never
# fails due to circular imports or heavy model modules.

_ENDPOINT_MODEL_MAP: list[tuple[str, str, str | None]] = [
    # Member detail
    (
        r"member--members--[^/]+___include=",
        "otf_api.models.members.member_detail.MemberDetail",
        "data",
    ),
    # Member membership
    (
        r"member--members--[^/]+--memberships",
        "otf_api.models.members.member_membership.MemberMembership",
        "data",
    ),
    # Member purchases (list)
    (
        r"member--members--[^/]+--purchases",
        "otf_api.models.members.member_purchases.MemberPurchase",
        "data[0]",
    ),
    # Body composition
    (
        r"member--members--[^/]+--body-composition",
        "otf_api.models.workouts.body_composition_list.BodyCompositionData",
        "data[0]",
    ),
    # Out of studio workout history
    (
        r"member--members--[^/]+--out-of-studio-workout",
        "otf_api.models.workouts.out_of_studio_workout_history.OutOfStudioWorkoutHistory",
        "data[0]",
    ),
    # Performance summary (individual)
    (
        r"v1--performance-summaries--[0-9a-f-]+",
        "otf_api.models.workouts.performance_summary.PerformanceSummary",
        None,
    ),
    # Telemetry (yuzu)
    (
        r"v1--performance--summary___classHistoryUuid=",
        "otf_api.models.workouts.telemetry.Telemetry",
        None,
    ),
    # HR history (telemetry history)
    (
        r"v1--physVars--maxHr--history",
        "otf_api.models.workouts.telemetry.TelemetryHistoryItem",
        "history[0]",
    ),
    # Studio detail
    (
        r"mobile--v1--studios--[^_]+(?:\.json)?$",
        "otf_api.models.studios.studio_detail.StudioDetail",
        "data",
    ),
    # Benchmarks (challenge tracker details)
    (
        r"challenges--v3--member--[^/]+--benchmarks",
        "otf_api.models.workouts.challenge_tracker_detail.FitnessBenchmark",
        "Dto[0]",
    ),
    # Challenge tracker (v3.1)
    (
        r"challenges--v3\.1--member--[^/]+",
        "otf_api.models.workouts.challenge_tracker_content.ChallengeTracker",
        "Dto",
    ),
    # Challenge participation
    (
        r"challenges--v1--member--[^/]+--participation",
        "otf_api.models.workouts.challenge_tracker_detail.FitnessBenchmark",
        "Dto[0]",
    ),
    # Lifetime stats
    (
        r"performance--v2--[^/]+--over-time",
        "otf_api.models.workouts.lifetime_stats.StatsResponse",
        "data",
    ),
    # Old bookings endpoint
    (
        r"member--members--[^/]+--bookings(?:_|\.json)",
        "otf_api.models.bookings.bookings.Booking",
        "data[0]",
    ),
    # New bookings endpoint (v1/bookings/me)
    (
        r"v1--bookings--me(?:[._]|$)",
        "otf_api.models.bookings.bookings_v2.BookingV2",
        "items[0]",
    ),
    # Classes
    (
        r"v1--classes",
        "otf_api.models.bookings.classes.OtfClass",
        "items[0]",
    ),
    # Studio services
    (
        r"member--studios--[^/]+--services",
        "otf_api.models.studios.studio_services.StudioService",
        "data[0]",
    ),
    # Favorite studios
    (
        r"member--members--[^/]+--favorite-studios",
        "otf_api.models.studios.studio_detail.StudioDetail",
        "data[0]",
    ),
    # Email notification settings
    (
        r"otfmailing--v2--preferences",
        "otf_api.models.members.notifications.EmailNotificationSettings",
        "data",
    ),
    # SMS notification settings
    (
        r"sms--v1--preferences",
        "otf_api.models.members.notifications.SmsNotificationSettings",
        "data",
    ),
    # Performance summaries list
    (
        r"v1--performance-summaries(?:\.json)?$",
        "otf_api.models.workouts.performance_summary.PerformanceSummary",
        "items[0]",
    ),
    # Studios by geo
    (
        r"mobile--v1--studios___",
        "otf_api.models.studios.studio_detail.StudioDetail",
        "data[0]",
    ),
]


def _get_model_class(model_path: str) -> type | None:
    """Lazily import and return a Pydantic model class by dotted path.

    Args:
        model_path: Fully qualified class path e.g. "otf_api.models.bookings.bookings.Booking".

    Returns:
        The class, or None if import fails.
    """
    try:
        parts = model_path.rsplit(".", 1)
        if len(parts) != 2:
            return None
        module_path, class_name = parts
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception:
        logger.debug("Failed to import model class %r", model_path, exc_info=True)
        return None


def _extract_payload(fixture: dict[str, Any], extraction_key: str | None) -> Any:  # noqa: ANN401
    """Extract the relevant payload from a fixture dict.

    Args:
        fixture: The raw fixture dict.
        extraction_key: Extraction hint (e.g. "data", "items[0]", "Dto[0]", None).

    Returns:
        The extracted payload, or None if extraction fails.
    """
    if extraction_key is None:
        return fixture

    try:
        # Handle indexed access patterns like "data[0]", "items[0]", "Dto[0]", "history[0]"
        if "[" in extraction_key:
            key, rest = extraction_key.split("[", 1)
            idx = int(rest.rstrip("]"))
            items = fixture.get(key, [])
            if not isinstance(items, list) or len(items) <= idx:
                return None
            return items[idx]

        # Simple key access
        return fixture.get(extraction_key)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# collect_real_values helper
# ---------------------------------------------------------------------------


def collect_real_values(
    data: dict[str, Any],
    mappings: list[FieldMapping],
    exclude_categories: frozenset[str] | None = None,
) -> set[str]:
    """Walk a raw dict and extract all values from mapped PII fields into a set.

    Includes URL-encoded variants (e.g. both ``%40`` and ``@`` forms of email).
    Includes case variants (lowercase and uppercase).

    Args:
        data: The raw (pre-anonymization) dict to scan.
        mappings: List of FieldMapping entries identifying which keys are PII.
        exclude_categories: Optional set of category names to exclude.
            For example, pass ``frozenset({"timestamp"})`` to skip timestamp
            fields (which pass through unchanged by design).

    Returns:
        A set of all real PII value strings found (with URL-encoded and case variants).
    """
    all_keys: set[str] = set()
    for mapping in mappings:
        if exclude_categories and mapping.category in exclude_categories:
            continue
        all_keys.update(mapping.json_keys)

    values: set[str] = set()
    _collect_values_recursive(data, all_keys, values)
    return values


def _collect_values_recursive(data: Any, pii_keys: set[str], values: set[str]) -> None:  # noqa: ANN401
    """Recursively walk data, collecting string values whose keys are in pii_keys."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in pii_keys and value is not None:
                _add_with_variants(str(value), values)
            else:
                _collect_values_recursive(value, pii_keys, values)
    elif isinstance(data, list):
        for item in data:
            _collect_values_recursive(item, pii_keys, values)


def _add_with_variants(value: str, values: set[str]) -> None:
    """Add a value and its URL-encoded/decoded variants to the set.

    Args:
        value: The string value to add.
        values: The set to add to (mutated in place).
    """
    if not value:
        return

    values.add(value)

    # URL-decode variant (handles %40 → @)
    decoded = unquote(value)
    if decoded != value:
        values.add(decoded)

    # URL-encode variant (handles @ → %40)
    # Only encode if the value contains chars that would be encoded
    encoded = quote(value, safe="")
    if encoded != value:
        values.add(encoded)


# ---------------------------------------------------------------------------
# PiiValidator
# ---------------------------------------------------------------------------

# Regex that matches the ", input_value=..." portion of a Pydantic ValidationError
# string.  Stripping this makes error normalization data-independent so that the same
# structural error on the raw vs. anonymized fixture compares as equal.
_PYDANTIC_INPUT_VALUE_RE = re.compile(r",\s*input_value=.*", re.DOTALL)


def _normalize_model_error(error: str) -> str:
    """Strip the data-specific ``input_value=…`` portion from a Pydantic error string.

    Pydantic's ValidationError string includes the actual field values, which differ
    between original and anonymized data.  This function strips everything after
    ``input_value=`` so two equivalent structural errors compare as equal.

    Args:
        error: Raw model-parse error string from ``_check_model_parsing``.

    Returns:
        A normalized string suitable for set membership testing.
    """
    return _PYDANTIC_INPUT_VALUE_RE.sub("", error)


class PiiValidator:
    """Validates anonymized fixture output for PII leaks and structural integrity.

    Args:
        known_real_values: Set of all real PII string values to scan for in output.
            Case-insensitive matching is performed — supply the original casing here.
    """

    def __init__(self, known_real_values: set[str]) -> None:
        self._real_values = known_real_values
        # Build lower-cased lookup: lower → original for reporting
        self._lower_to_real: dict[str, str] = {}
        for v in known_real_values:
            if isinstance(v, str) and v:
                self._lower_to_real[v.lower()] = v

    def validate_file(
        self,
        original: dict,
        anonymized: dict,
        filename: str,
        model_hint: str | None = None,
    ) -> ValidationResult:
        """Validate one anonymized fixture file.

        Performs four checks:
        1. Scan anonymized dict for leaked real PII values
        2. Scan the filename itself for leaked real PII values
        3. Check structural integrity (same keys, types, null preservation)
        4. Attempt model parsing (best-effort)

        Args:
            original: The original (pre-anonymization) fixture dict.
            anonymized: The anonymized fixture dict to validate.
            filename: The filename (used for leak scanning and ``LeakReport.file``).
                Should be the *anonymized* filename so the filename leak check
                accurately reflects what was actually written.
            model_hint: Optional alternative path used only for the Pydantic model
                pattern lookup (step 4).  Pass the *original* filename here when
                filenames have been anonymized — the anonymized name won't match
                endpoint patterns.  If None, *filename* is used for model lookup.

        Returns:
            A ValidationResult summarising all findings.
        """
        leaks: list[LeakReport] = []
        structural_errors: list[str] = []
        model_parse_errors: list[str] = []

        # 1. Check anonymized body for leaks
        leaks.extend(self._check_for_leaks(anonymized, filename))

        # 2. Check filename for leaks
        for lower_val, real_val in self._lower_to_real.items():
            if lower_val in filename.lower():
                leaks.append(
                    LeakReport(
                        file=filename,
                        field_path="<filename>",
                        real_value=real_val,
                        category="filename",
                    )
                )

        # 3. Check structural integrity
        structural_errors.extend(self._check_structural_integrity(original, anonymized))

        # 4. Attempt model parsing (best-effort)
        # Use model_hint (original path) for pattern matching when filenames are anonymized.
        endpoint_path = model_hint if model_hint is not None else filename
        anon_errors = self._check_model_parsing(anonymized, endpoint_path)

        # Only report model errors that are NOT pre-existing in the original data.
        # Some fixtures have missing required fields in the raw data (e.g. incomplete
        # sub-objects returned by the API).  These are not regressions introduced by
        # anonymization.  Pydantic error strings include input_value which differs
        # between original and anonymized data, so we normalize to just the error
        # type and field path before comparing.
        orig_errors_normalized = {_normalize_model_error(e) for e in self._check_model_parsing(original, endpoint_path)}
        for err in anon_errors:
            if _normalize_model_error(err) not in orig_errors_normalized:
                model_parse_errors.append(err)

        passed = not leaks and not structural_errors

        return ValidationResult(
            passed=passed,
            leaks=leaks,
            structural_errors=structural_errors,
            model_parse_errors=model_parse_errors,
        )

    def validate_batch(self, original_dir: Path, anonymized_dir: Path) -> ValidationResult:
        """Validate all JSON files in a batch directory pair.

        For each file in *anonymized_dir*, finds the matching file in *original_dir*
        and runs ``validate_file``.

        Args:
            original_dir: Directory containing original (pre-anonymization) fixtures.
            anonymized_dir: Directory containing anonymized fixtures.

        Returns:
            A combined ValidationResult for all files in the batch.
        """
        all_leaks: list[LeakReport] = []
        all_structural: list[str] = []
        all_parse: list[str] = []

        for anon_file in sorted(anonymized_dir.glob("**/*.json")):
            relative = anon_file.relative_to(anonymized_dir)
            orig_file = original_dir / relative

            if not orig_file.exists():
                all_structural.append(f"{relative}: no matching original file found")
                continue

            try:
                with orig_file.open() as f:
                    original = json.load(f)
                with anon_file.open() as f:
                    anonymized = json.load(f)
            except Exception as exc:
                all_structural.append(f"{relative}: failed to load JSON: {exc}")
                continue

            result = self.validate_file(original, anonymized, str(relative))
            all_leaks.extend(result.leaks)
            all_structural.extend(result.structural_errors)
            all_parse.extend(result.model_parse_errors)

        passed = not all_leaks and not all_structural

        return ValidationResult(
            passed=passed,
            leaks=all_leaks,
            structural_errors=all_structural,
            model_parse_errors=all_parse,
        )

    def _check_for_leaks(self, data: dict, filename: str) -> list[LeakReport]:
        """Recursively scan all string values in the anonymized dict for real PII values.

        Case-insensitive matching against all known real values.

        Args:
            data: The anonymized fixture dict to scan.
            filename: The filename (used in LeakReport.file).

        Returns:
            List of LeakReports for any found leaks.
        """
        leaks: list[LeakReport] = []
        self._scan_recursive(data, filename, "", leaks)
        return leaks

    def _scan_recursive(
        self,
        node: Any,  # noqa: ANN401
        filename: str,
        path: str,
        leaks: list[LeakReport],
    ) -> None:
        """Recursively walk *node*, appending LeakReports to *leaks* for any matches."""
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}" if path else key
                self._scan_recursive(value, filename, child_path, leaks)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                child_path = f"{path}[{i}]"
                self._scan_recursive(item, filename, child_path, leaks)
        elif isinstance(node, str):
            lower_node = node.lower()
            for lower_val, real_val in self._lower_to_real.items():
                if lower_val in lower_node:
                    leaks.append(
                        LeakReport(
                            file=filename,
                            field_path=path,
                            real_value=real_val,
                            category="string_scan",
                        )
                    )
        elif isinstance(node, int | float) and not isinstance(node, bool):
            str_node = str(node).lower()
            for lower_val, real_val in self._lower_to_real.items():
                if lower_val == str_node:
                    leaks.append(
                        LeakReport(
                            file=filename,
                            field_path=path,
                            real_value=real_val,
                            category="numeric_scan",
                        )
                    )

    def _check_structural_integrity(self, original: dict, anonymized: dict, path: str = "") -> list[str]:
        """Verify same keys exist, same types, same nesting depth, and nulls are preserved.

        Args:
            original: Original fixture dict.
            anonymized: Anonymized fixture dict.
            path: Current dot-path prefix for error messages.

        Returns:
            List of error message strings.
        """
        errors: list[str] = []

        if not isinstance(original, dict) or not isinstance(anonymized, dict):
            # If both are non-dicts, check type consistency
            if type(original) != type(anonymized):  # noqa: E721
                errors.append(f"{path}: type changed from {type(original).__name__} to {type(anonymized).__name__}")
            return errors

        original_keys = set(original.keys())
        anonymized_keys = set(anonymized.keys())

        missing_keys = original_keys - anonymized_keys
        extra_keys = anonymized_keys - original_keys

        for key in missing_keys:
            key_path = f"{path}.{key}" if path else key
            errors.append(f"{key_path}: key missing from anonymized output")

        for key in extra_keys:
            key_path = f"{path}.{key}" if path else key
            errors.append(f"{key_path}: unexpected key in anonymized output")

        for key in original_keys & anonymized_keys:
            orig_val = original[key]
            anon_val = anonymized[key]
            key_path = f"{path}.{key}" if path else key

            # Null preservation
            if orig_val is None and anon_val is not None:
                errors.append(f"{key_path}: original was null but anonymized is {type(anon_val).__name__}")
                continue
            if orig_val is not None and anon_val is None:
                errors.append(f"{key_path}: original was {type(orig_val).__name__} but anonymized is null")
                continue

            if orig_val is None and anon_val is None:
                continue

            # Type check
            if type(orig_val) != type(anon_val):  # noqa: E721
                # Allow int/float interchangeability
                if not (isinstance(orig_val, int | float) and isinstance(anon_val, int | float)):
                    errors.append(
                        f"{key_path}: type changed from {type(orig_val).__name__} to {type(anon_val).__name__}"
                    )
                    continue

            # Recurse into dicts
            if isinstance(orig_val, dict) and isinstance(anon_val, dict):
                errors.extend(self._check_structural_integrity(orig_val, anon_val, key_path))
            elif isinstance(orig_val, list) and isinstance(anon_val, list):
                if len(orig_val) != len(anon_val):
                    errors.append(f"{key_path}: list length changed from {len(orig_val)} to {len(anon_val)}")
                else:
                    for i, (orig_item, anon_item) in enumerate(zip(orig_val, anon_val)):
                        item_path = f"{key_path}[{i}]"
                        if isinstance(orig_item, dict) and isinstance(anon_item, dict):
                            errors.extend(self._check_structural_integrity(orig_item, anon_item, item_path))
                        elif type(orig_item) != type(anon_item):  # noqa: E721
                            if not (isinstance(orig_item, int | float) and isinstance(anon_item, int | float)):
                                orig_type = type(orig_item).__name__
                                anon_type = type(anon_item).__name__
                                errors.append(f"{item_path}: type changed from {orig_type} to {anon_type}")

        return errors

    def _check_model_parsing(self, anonymized: dict, endpoint_path: str) -> list[str]:
        """Attempt to parse the anonymized dict through the corresponding Pydantic model.

        This is a best-effort check. If the fixture cannot be matched to a model,
        or if the model requires complex setup, errors are reported but do not fail
        the overall validation.

        Args:
            anonymized: The anonymized fixture dict.
            endpoint_path: The fixture filename/path used to look up the model.

        Returns:
            List of model parse error strings.
        """
        errors: list[str] = []

        # Find a matching endpoint pattern
        model_path: str | None = None
        extraction_key: str | None = None

        for pattern, mp, ek in _ENDPOINT_MODEL_MAP:
            if re.search(pattern, endpoint_path):
                model_path = mp
                extraction_key = ek
                break

        if model_path is None:
            logger.debug("No model mapping found for endpoint path %r", endpoint_path)
            return errors

        model_class = _get_model_class(model_path)
        if model_class is None:
            errors.append(f"Could not import model class {model_path}")
            return errors

        payload = _extract_payload(anonymized, extraction_key)
        if payload is None:
            errors.append(f"Could not extract payload from fixture using key {extraction_key!r} for {endpoint_path}")
            return errors

        if not isinstance(payload, dict):
            # Can't parse a non-dict
            return errors

        try:
            model_class.model_validate(payload)
        except Exception as exc:
            errors.append(f"Model parse failed for {model_path}: {exc}")

        return errors
