"""Batch anonymization for the OTF API fixture anonymization pipeline.

Processes a full directory of raw fixture files, writing anonymized output
alongside a replacement map and running the PII validator on the result.

Public API:
    - ``BatchResult`` — dataclass summarising the batch run
    - ``anonymize_batch`` — process an entire fixture corpus
"""

import dataclasses
import json
import logging
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

from otf_api.anonymize._io import atomic_write as _atomic_write
from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer
from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import FIELD_MAPPINGS
from otf_api.anonymize.validator import LeakReport, PiiValidator, ValidationResult, collect_real_values

logger = logging.getLogger(__name__)

# The member UUID seed hint — first UUID-like value collected from files.
# Used to derive a deterministic default seed.
_UUID_SEED_KEY = "memberUUId"

# Regex matching a standard UUID4-format string (8-4-4-4-12 hex digits)
_UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


@dataclasses.dataclass
class BatchResult:
    """Summarises the result of a full-batch anonymization run.

    Attributes:
        files_processed: Number of JSON files successfully anonymized.
        files_skipped: Number of JSON files skipped due to malformed JSON.
        output_dir: Path to the directory containing anonymized output.
        replacement_map_path: Path to the serialized replacement map file.
        validation: ValidationResult from the post-batch PII validator run.
    """

    files_processed: int
    files_skipped: int
    output_dir: Path
    replacement_map_path: Path
    validation: ValidationResult


def _derive_seed_from_uuid(uuid_str: str) -> int:
    """Derive a deterministic integer seed from a UUID string.

    Args:
        uuid_str: A UUID string (e.g. "7b1cf060-fd27-45ab-b820-fdcdefa4ee23").

    Returns:
        A positive integer seed derived from the UUID.
    """
    # Remove hyphens and parse the hex string as an integer, then truncate to 32-bit
    return int(uuid_str.replace("-", ""), 16) % (2**32)


def _find_first_member_uuid(input_dir: Path) -> str | None:
    """Scan JSON files for the first memberUUId value found.

    Scans files in sorted order so the seed is deterministic across runs.

    Args:
        input_dir: The directory to scan.

    Returns:
        The first memberUUId string found, or None if none is found.
    """
    for json_file in sorted(input_dir.rglob("*.json")):
        if json_file.name == "_meta.json":
            continue
        try:
            with json_file.open() as f:
                data = json.load(f)
            uuid_val = _find_uuid_recursive(data)
            if uuid_val:
                return uuid_val
        except Exception:
            continue
    return None


def _find_uuid_recursive(data: object) -> str | None:
    """Recursively search for a memberUUId value in nested data.

    Args:
        data: JSON-compatible data structure to search.

    Returns:
        The first memberUUId string found, or None.
    """
    if isinstance(data, dict):
        if _UUID_SEED_KEY in data and isinstance(data[_UUID_SEED_KEY], str):
            return data[_UUID_SEED_KEY]
        for value in data.values():
            result = _find_uuid_recursive(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_uuid_recursive(item)
            if result:
                return result
    return None


def _preseed_uuids_from_filenames(input_dir: Path, anonymizer: Anonymizer) -> int:
    """Extract all UUID-format strings from fixture filenames and pre-seed the replacement map.

    Fixtures like ``challenges--v3--member--<uuid>--benchmarks*.json`` embed the
    member UUID in the filename but not in the response body.  Pre-seeding ensures
    the replacement map contains a fake UUID for the real one *before* filename
    anonymization runs, so ``anonymize_filename`` can substitute it.

    Only UUIDs that match the standard 8-4-4-4-12 hex pattern are extracted.
    Each unique UUID is registered once; subsequent calls for the same UUID
    return the cached fake.

    Args:
        input_dir: The directory to scan for fixture filenames.
        anonymizer: The Anonymizer whose replacement map will be pre-seeded.

    Returns:
        The number of unique UUIDs pre-seeded.
    """
    seen_uuids: set[str] = set()
    for json_file in sorted(input_dir.rglob("*.json")):
        relative = str(json_file.relative_to(input_dir))
        for match in _UUID_PATTERN.finditer(relative):
            uuid_str = match.group(0).lower()
            if uuid_str not in seen_uuids:
                seen_uuids.add(uuid_str)
                # Force the UUID into the replacement map via anonymize_value
                # We use the memberUUId key so it is treated as identity_uuid
                anonymizer.anonymize_value("memberUUId", uuid_str)

    logger.debug("Pre-seeded %d UUIDs from filenames", len(seen_uuids))
    return len(seen_uuids)


_MIN_PII_LENGTH = 8
"""Minimum character length for a value to be considered a meaningful PII leak.

Short values like state codes ("KS"), single digits ("0"), gender codes ("M"),
common first names ("Blair", "Bobby", "Erika" — all ≤7 chars) will produce
false-positive leak reports because:
  1. They appear as substrings in safe metadata (studio names, etc.)
  2. Faker's name generator draws from the same name pool and can accidentally
     generate a name that matches a real name in the corpus.

8 characters is the practical threshold: short enough to catch phone numbers
(10 digits) and emails; long enough to exclude common first names (7 chars
or fewer) and 2-letter state codes from scanning. Note: numeric member IDs
(6-7 digits) fall below this threshold and are not scanned for leaks.
"""


def _collect_all_real_values(input_dir: Path) -> set[str]:
    """Collect all real PII values from the entire input corpus.

    Values shorter than ``_MIN_PII_LENGTH`` characters are excluded to prevent
    false-positive leak reports from short codes (state abbreviations, gender
    codes, single digits) that appear as substrings everywhere.

    Args:
        input_dir: The directory containing raw fixture files.

    Returns:
        A set of all real PII value strings found across all files.
    """
    all_values: set[str] = set()
    for json_file in sorted(input_dir.rglob("*.json")):
        if json_file.name.startswith("_"):
            continue
        try:
            with json_file.open() as f:
                data = json.load(f)
            # Exclude categories that are intentionally passed through unchanged
            # or that produce false-positive leak reports:
            # - timestamp: offset logic is deferred; timestamps pass through as-is
            # - image_url: not a privacy risk for scanning purposes
            # - address: city/state/country components (e.g. "Wichita") appear in
            #   KNOWN_SAFE studio name fields (e.g. "studioName": "Wichita East, KS")
            #   and would produce thousands of false-positive leak reports.
            #   Address fields ARE anonymized in body output; we just don't scan for
            #   them appearing as substrings in safe metadata strings.
            file_values = collect_real_values(
                data,
                FIELD_MAPPINGS,
                exclude_categories=frozenset({"timestamp", "image_url", "address"}),
            )
            # Filter out short values that will cause false-positive scans
            all_values.update(v for v in file_values if len(v) >= _MIN_PII_LENGTH)
        except Exception:
            continue
    return all_values


def _anonymize_meta(meta: dict, anonymizer: Anonymizer) -> dict:
    """Anonymize the _meta.json file by substituting PII from params and file fields.

    Uses the replacement map that has been built up during body processing to
    substitute known real values from ``params`` and ``file`` fields.

    Args:
        meta: The parsed _meta.json dict.
        anonymizer: The Anonymizer instance (with replacement map populated).

    Returns:
        A new dict with PII values replaced in params and file fields.
    """
    result = dict(meta)

    if "files" in result and isinstance(result["files"], list):
        anon_files = []
        for entry in result["files"]:
            anon_entry = dict(entry)
            if "params" in anon_entry and isinstance(anon_entry["params"], str):
                anon_entry["params"] = anonymizer.anonymize_url(anon_entry["params"])
            if "file" in anon_entry and isinstance(anon_entry["file"], str):
                anon_entry["file"] = anonymizer.anonymize_filename(anon_entry["file"])
            if "path" in anon_entry and isinstance(anon_entry["path"], str):
                anon_entry["path"] = anonymizer.anonymize_url(anon_entry["path"])
            anon_files.append(anon_entry)
        result["files"] = anon_files

    return result


def anonymize_batch(
    input_dir: Path,
    output_dir: Path,
    *,
    seed: int | None = None,
    config: AnonymizeConfig | None = None,
) -> BatchResult:
    """Anonymize all JSON fixtures in *input_dir*, writing results to *output_dir*.

    Processing steps:
    1. Derive a seed from the first member UUID found (unless *seed* or *config.seed* overrides)
    2. Instantiate the Anonymizer with a shared ReplacementMap for referential integrity
    3. Process each JSON file in sorted order: read, anonymize body, anonymize filename, write
    4. Skip malformed JSON files with a warning
    5. Anonymize _meta.json (PII in params and file fields)
    6. Write _anonymization_map.json with the replacement map
    7. Run the PII validator on the full output corpus
    8. Return a BatchResult summary

    On write failure (disk full, permission error): removes the partial output directory
    and raises the original exception with a clear error message.

    Args:
        input_dir: Directory containing raw fixture files.
        output_dir: Directory to write anonymized output. Created if it doesn't exist.
        seed: Optional integer seed for reproducible output. Overrides any seed in *config*.
        config: Optional AnonymizeConfig. If None, a default config is created.

    Returns:
        A BatchResult summarising the run.

    Raises:
        OSError: If output_dir cannot be created or written to (partial output cleaned up).
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # ------------------------------------------------------------------
    # Step 1: Resolve seed
    # ------------------------------------------------------------------
    effective_seed = seed
    if effective_seed is None and config is not None:
        effective_seed = config.seed
    if effective_seed is None:
        first_uuid = _find_first_member_uuid(input_dir)
        if first_uuid:
            effective_seed = _derive_seed_from_uuid(first_uuid)
            logger.info("Derived seed %d from member UUID %s", effective_seed, first_uuid)
        else:
            logger.warning("No memberUUId found in fixtures; using random seed")

    # ------------------------------------------------------------------
    # Step 2: Build anonymizer
    # ------------------------------------------------------------------
    if config is None:
        effective_config = AnonymizeConfig(seed=effective_seed)
    else:
        effective_config = dataclasses.replace(config, seed=effective_seed)

    generators = FakeDataGenerators(seed=effective_seed)
    anonymizer = Anonymizer(config=effective_config, generators=generators, mappings=FIELD_MAPPINGS)

    # ------------------------------------------------------------------
    # Step 3: Collect all real values for the validator (before processing)
    # ------------------------------------------------------------------
    logger.info("Collecting real PII values from %s", input_dir)
    all_real_values = _collect_all_real_values(input_dir)
    logger.info("Found %d distinct real PII values", len(all_real_values))

    # ------------------------------------------------------------------
    # Step 3b: Pre-seed the replacement map with UUIDs from filenames
    # Some fixtures (e.g. challenges endpoints) embed the member UUID only in
    # the filename, not in the response body.  Pre-seeding ensures that every
    # UUID in a filename gets a fake UUID in the replacement map before
    # anonymize_filename() runs.
    # ------------------------------------------------------------------
    n_preseeded = _preseed_uuids_from_filenames(input_dir, anonymizer)
    logger.info("Pre-seeded replacement map with %d filename UUIDs", n_preseeded)

    files_processed = 0
    files_skipped = 0

    # ------------------------------------------------------------------
    # Step 5: Anonymize and validate all files in memory before writing
    # ------------------------------------------------------------------
    all_json_files = sorted(input_dir.rglob("*.json"))
    data_files = [f for f in all_json_files if not f.name.startswith("_")]

    # Tuples of (anon_output_path, anon_json_str, orig_path_str, anon_path_str, orig_dict, anon_dict)
    # Accumulated in memory so no PII hits disk until validation passes.
    pending_writes: list[tuple[Path, str, str, str, dict, dict]] = []

    for json_file in data_files:
        relative_path = json_file.relative_to(input_dir)

        # Read and parse
        try:
            raw_text = json_file.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Skipping malformed JSON file %s: %s", json_file, exc)
            files_skipped += 1
            continue

        # Anonymize the body
        context = str(relative_path)
        anon_data = anonymizer.anonymize_dict(data, context=context)

        # Anonymize the filename using the now-populated replacement map
        anon_relative_str = anonymizer.anonymize_filename(str(relative_path))
        anon_output_path = output_dir / anon_relative_str

        anon_json_str = json.dumps(anon_data, indent=2, ensure_ascii=False)
        pending_writes.append((anon_output_path, anon_json_str, str(relative_path), anon_relative_str, data, anon_data))
        files_processed += 1
        logger.debug("Anonymized %s -> %s", relative_path, anon_relative_str)

    # ------------------------------------------------------------------
    # Step 6: Validate all anonymized data in memory (before any disk writes)
    # ------------------------------------------------------------------
    validator = PiiValidator(known_real_values=all_real_values)
    all_leaks: list[LeakReport] = []
    all_structural: list[str] = []
    all_parse: list[str] = []

    for _anon_path, _anon_json, orig_path_str, anon_path_str, original_data, anon_data in pending_writes:
        pair_result = validator.validate_file(
            original_data,
            anon_data,
            filename=anon_path_str,
            model_hint=orig_path_str,
        )
        all_leaks.extend(pair_result.leaks)
        all_structural.extend(pair_result.structural_errors)
        all_parse.extend(pair_result.model_parse_errors)

    # Also check anonymized filenames for PII leaks
    lower_to_real: dict[str, str] = {}
    for v in all_real_values:
        if isinstance(v, str) and v:
            lower_to_real[v.lower()] = v
            decoded = unquote(v)
            if decoded != v:
                lower_to_real[decoded.lower()] = decoded

    for _anon_path, _anon_json, _orig_path_str, anon_path_str, _orig, _anon in pending_writes:
        lower_filename = anon_path_str.lower()
        for lower_val, real_val in lower_to_real.items():
            if lower_val in lower_filename:
                all_leaks.append(
                    LeakReport(
                        file=anon_path_str,
                        field_path="<filename>",
                        real_value=real_val,
                        category="filename",
                    )
                )

    validation_result = ValidationResult(
        passed=not all_leaks and not all_structural,
        leaks=all_leaks,
        structural_errors=all_structural,
        model_parse_errors=all_parse,
    )

    if not validation_result.passed:
        logger.error(
            "Validation failed: %d leaks, %d structural errors — no files written to disk",
            len(validation_result.leaks),
            len(validation_result.structural_errors),
        )
        return BatchResult(
            files_processed=files_processed,
            files_skipped=files_skipped,
            output_dir=output_dir,
            replacement_map_path=output_dir / "_anonymization_map.json",
            validation=validation_result,
        )

    # ------------------------------------------------------------------
    # Step 7: Write all validated files to disk
    # ------------------------------------------------------------------
    output_dir_existed = output_dir.exists()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        for anon_output_path, anon_json_str, *_ in pending_writes:
            _atomic_write(anon_output_path, anon_json_str)

        # ------------------------------------------------------------------
        # Step 8: Anonymize and write _meta.json if it exists
        # ------------------------------------------------------------------
        meta_src = input_dir / "_meta.json"
        if meta_src.exists():
            try:
                with meta_src.open(encoding="utf-8") as f:
                    meta = json.load(f)
                anon_meta = _anonymize_meta(meta, anonymizer)
                meta_dest = output_dir / "_meta.json"
                _atomic_write(meta_dest, json.dumps(anon_meta, indent=2, ensure_ascii=False))
                logger.debug("Anonymized _meta.json")
            except OSError:
                raise
            except Exception as exc:
                logger.warning("Failed to anonymize _meta.json: %s", exc)

        # ------------------------------------------------------------------
        # Step 9: Write replacement map
        # ------------------------------------------------------------------
        replacement_map_path = output_dir / "_anonymization_map.json"
        raw_map = anonymizer.replacement_map.to_json()
        # Invert to {fake: position_hint} to avoid writing real PII to disk.
        # NOTE: this format is NOT compatible with ReplacementMap.from_json().
        safe_map: dict[str, str] = {}
        for idx, (real_val, fake_val) in enumerate(raw_map.items()):
            safe_map[fake_val] = f"position:{idx}"
        _atomic_write(replacement_map_path, json.dumps(safe_map, indent=2, ensure_ascii=False))
        logger.info("Wrote replacement map with %d entries to %s", len(safe_map), replacement_map_path)

    except (OSError, RecursionError, ValueError) as exc:
        if output_dir_existed:
            logger.error(
                "Write failure at %s: %s — pre-existing output directory preserved",
                output_dir,
                exc,
            )
            raise OSError(f"Batch anonymization failed (pre-existing output dir preserved): {exc}") from exc
        logger.error("Write failure, cleaning up partial output at %s: %s", output_dir, exc)
        try:
            shutil.rmtree(output_dir)
        except Exception as cleanup_exc:
            logger.warning("Cleanup failed: %s; partial output may remain at %s", cleanup_exc, output_dir)
        raise OSError(f"Batch anonymization failed (partial output cleaned up): {exc}") from exc

    logger.info(
        "Batch complete: %d processed, %d skipped, %d leaks, %d structural errors, %d model errors",
        files_processed,
        files_skipped,
        len(validation_result.leaks),
        len(validation_result.structural_errors),
        len(validation_result.model_parse_errors),
    )

    return BatchResult(
        files_processed=files_processed,
        files_skipped=files_skipped,
        output_dir=output_dir,
        replacement_map_path=replacement_map_path,
        validation=validation_result,
    )
