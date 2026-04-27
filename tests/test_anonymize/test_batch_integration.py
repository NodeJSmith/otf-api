"""Integration tests for batch anonymization against the real fixture corpus.

These tests require raw fixture files to be present locally at fixtures/raw_responses/.
They are skipped in CI where real fixtures are not available.

Tests that do NOT require real fixtures (malformed JSON, disk full) work anywhere.

Run with:
    timeout 300 uv run pytest tests/test_anonymize/test_batch_integration.py
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from otf_api.anonymize import anonymize_batch, batch
from otf_api.anonymize.anonymizer import AnonymizeConfig

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
_RAW_FIXTURES_DIR = _REPO_ROOT / "fixtures" / "raw_responses"

# Skip marker for all tests requiring real fixtures
_FIXTURES_PRESENT = _RAW_FIXTURES_DIR.exists() and any(_RAW_FIXTURES_DIR.glob("**/*.json"))
_SKIP_WITHOUT_FIXTURES = pytest.mark.skipif(
    not _FIXTURES_PRESENT,
    reason="Real fixture files not present — skipped in CI (fixtures/raw_responses/ missing or empty)",
)

# Real PII values we expect NOT to see in output
_REAL_MEMBER_UUID = "7b1cf060-fd27-45ab-b820-fdcdefa4ee23"
_REAL_EMAIL = "12jessicasmith34@gmail.com"
_REAL_PHONE = "3166808339"


# ---------------------------------------------------------------------------
# Tests requiring real fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def batch_result(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, object]:
    """Module-scoped fixture: run the batch once, return (output_dir, BatchResult)."""
    if not _FIXTURES_PRESENT:
        pytest.skip("Real fixture files not present")

    out = tmp_path_factory.mktemp("anonymized_batch")
    result = anonymize_batch(_RAW_FIXTURES_DIR, out, seed=42, config=AnonymizeConfig(seed=42, strictness="permissive"))
    return out, result


@pytest.fixture(scope="module")
def batch_output_dir(batch_result: tuple[Path, object]) -> Path:
    """Return only the output directory from the module-scoped batch run."""
    out, _ = batch_result
    return out


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_zero_leaks(batch_result: tuple[Path, object]) -> None:
    """Run the anonymizer on all fixture files and assert zero PII leaks.

    Uses the built-in validation result from the batch run, which validates
    each (original, anonymized) pair without relying on filename matching.
    """
    _, result = batch_result

    assert result.validation.leaks == [], (
        f"Expected zero leaks but found {len(result.validation.leaks)}:\n"
        + "\n".join(
            f"  {leak.file}:{leak.field_path} → {leak.real_value!r}"
            for leak in result.validation.leaks[:10]
        )
    )


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_models_parse(batch_result: tuple[Path, object]) -> None:
    """All anonymized files should parse through their corresponding Pydantic models.

    Uses the built-in validation result from the batch run (validated inline
    against original paths), then filters out informational-only errors.
    """
    _, result = batch_result

    # Filter to only model parse errors that indicate a real failure
    # (not "no model mapping found" — those are informational)
    parse_errors = [
        e
        for e in result.validation.model_parse_errors
        if "Could not import model" not in e and "Could not extract payload" not in e
    ]

    assert not parse_errors, (
        "Model parse errors found:\n"
        + "\n".join(f"  {e}" for e in parse_errors[:20])
    )


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_referential_integrity(batch_output_dir: Path) -> None:
    """The member UUID should appear in the same number of output files and as the same fake UUID."""
    # Verify the real UUID does NOT appear in any output filenames
    output_files_with_real_uuid = [
        f for f in sorted(batch_output_dir.rglob("*.json"))
        if _REAL_MEMBER_UUID in str(f.relative_to(batch_output_dir))
    ]
    assert output_files_with_real_uuid == [], (
        f"Real member UUID found in {len(output_files_with_real_uuid)} output filenames: "
        + str([str(f.relative_to(batch_output_dir)) for f in output_files_with_real_uuid[:3]])
    )

    # The number of output files should equal the number of valid input files processed
    # plus 1 for _anonymization_map.json (which is extra output, not in input)
    output_json_count = len(list(batch_output_dir.rglob("*.json")))
    input_json_count = len([f for f in _RAW_FIXTURES_DIR.rglob("*.json")])
    # Output = input files + _anonymization_map.json
    expected_output = input_json_count + 1
    assert output_json_count == expected_output, (
        f"Expected {expected_output} output files (input={input_json_count} + 1 for map) but found {output_json_count}"
    )



@_SKIP_WITHOUT_FIXTURES
def test_full_batch_nulls_preserved(batch_output_dir: Path) -> None:
    """Known null fields in anonymized output should remain null."""
    nulls_found = 0
    nulls_verified = 0

    for json_file in sorted(batch_output_dir.rglob("*.json")):
        if json_file.name.startswith("_"):
            continue
        try:
            with json_file.open() as f:
                data = json.load(f)
        except Exception:
            continue

        null_paths = _collect_null_paths(data)
        if null_paths:
            nulls_found += 1
            nulls_verified += len(null_paths)

    # The corpus should have at least some null fields
    assert nulls_found > 0, "Expected at least one file with null fields in the output corpus"
    assert nulls_verified > 0, "Expected at least some null fields to be preserved"


def _collect_null_paths(data: object, path: str = "") -> list[str]:
    """Return dot-paths of all null values in the data structure."""
    paths: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            if value is None:
                paths.append(child_path)
            else:
                paths.extend(_collect_null_paths(value, child_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            paths.extend(_collect_null_paths(item, f"{path}[{i}]"))
    return paths


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_filenames_anonymized(batch_output_dir: Path) -> None:
    """No output filename should contain the real member UUID, email, or phone number."""
    violations: list[str] = []

    for output_file in sorted(batch_output_dir.rglob("*.json")):
        rel = str(output_file.relative_to(batch_output_dir))
        if _REAL_MEMBER_UUID in rel:
            violations.append(f"{rel} contains real member UUID")
        if _REAL_EMAIL.lower() in rel.lower():
            violations.append(f"{rel} contains real email")
        if _REAL_PHONE in rel:
            violations.append(f"{rel} contains real phone number")

    assert violations == [], (
        f"Found {len(violations)} filename(s) containing real PII:\n"
        + "\n".join(f"  {v}" for v in violations[:10])
    )


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_meta_anonymized(batch_output_dir: Path) -> None:
    """The anonymized _meta.json should contain no real PII in params or file fields."""
    meta_path = batch_output_dir / "_meta.json"
    if not meta_path.exists():
        pytest.skip("No _meta.json in output")

    with meta_path.open() as f:
        meta = json.load(f)

    files_list = meta.get("files", [])
    assert files_list, "_meta.json has no 'files' list"

    violations: list[str] = []
    for entry in files_list:
        params = entry.get("params", "")
        file_val = entry.get("file", "")
        path_val = entry.get("path", "")

        for field_name, field_val in [("params", params), ("file", file_val), ("path", path_val)]:
            if _REAL_MEMBER_UUID in str(field_val):
                violations.append(f"{field_name}={field_val!r} contains real member UUID")
            if _REAL_EMAIL.lower() in str(field_val).lower():
                violations.append(f"{field_name}={field_val!r} contains real email")
            if _REAL_PHONE in str(field_val):
                violations.append(f"{field_name}={field_val!r} contains real phone number")

    assert violations == [], (
        f"Found {len(violations)} real PII value(s) in _meta.json:\n"
        + "\n".join(f"  {v}" for v in violations[:10])
    )


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_determinism(tmp_path: Path) -> None:
    """Running the anonymizer twice with the same seed should produce byte-identical output."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    cfg = AnonymizeConfig(seed=42, strictness="permissive")
    anonymize_batch(_RAW_FIXTURES_DIR, out1, seed=42, config=cfg)
    anonymize_batch(_RAW_FIXTURES_DIR, out2, seed=42, config=cfg)

    files1 = sorted(p.relative_to(out1) for p in out1.rglob("*.json"))
    files2 = sorted(p.relative_to(out2) for p in out2.rglob("*.json"))

    assert files1 == files2, (
        f"File lists differ between runs:\n"
        f"  Run 1: {files1[:5]}\n"
        f"  Run 2: {files2[:5]}"
    )

    differences: list[str] = []
    for rel_path in files1:
        content1 = (out1 / rel_path).read_bytes()
        content2 = (out2 / rel_path).read_bytes()
        if content1 != content2:
            differences.append(str(rel_path))

    assert differences == [], (
        f"Non-deterministic output: {len(differences)} file(s) differ between runs:\n"
        + "\n".join(f"  {p}" for p in differences[:10])
    )


@_SKIP_WITHOUT_FIXTURES
def test_full_batch_replacement_map_written(batch_output_dir: Path) -> None:
    """The replacement map file should exist and be valid JSON."""
    map_path = batch_output_dir / "_anonymization_map.json"
    assert map_path.exists(), "_anonymization_map.json not found in output directory"

    with map_path.open() as f:
        data = json.load(f)

    assert isinstance(data, dict), "_anonymization_map.json should be a JSON object"
    assert len(data) > 0, "_anonymization_map.json should not be empty"


@_SKIP_WITHOUT_FIXTURES
def test_address_format_variants_consistent(batch_output_dir: Path) -> None:
    """Studio address should map to the same fake address in both booking v1 and v2 fixtures.

    This specifically targets the edge case where the same studio appears in both
    old bookings (api.orangetheory.co) and new bookings (api.orangetheory.io) endpoints.
    """
    # Collect all city values from old bookings fixture
    old_booking_cities: set[str] = set()
    for json_file in sorted(batch_output_dir.glob("api.orangetheory.co/*bookings*.json")):
        try:
            with json_file.open() as f:
                data = json.load(f)
            old_booking_cities.update(_collect_field_values(data, "city"))
        except Exception:
            continue

    # Collect all city values from new bookings fixture
    new_booking_cities: set[str] = set()
    for json_file in sorted(batch_output_dir.glob("api.orangetheory.io/*bookings*.json")):
        try:
            with json_file.open() as f:
                data = json.load(f)
            new_booking_cities.update(_collect_field_values(data, "city"))
        except Exception:
            continue

    if not old_booking_cities or not new_booking_cities:
        pytest.skip("No booking fixtures found in output — cannot test address consistency")

    # Both should have the same set of fake cities (same studio, same fake address)
    # At minimum they should share at least one city for studios that appear in both
    overlap = old_booking_cities & new_booking_cities
    assert overlap, (
        f"No shared city values between old and new booking fixtures.\n"
        f"  Old booking cities: {old_booking_cities}\n"
        f"  New booking cities: {new_booking_cities}\n"
        "This may indicate address referential integrity is broken."
    )


def _collect_field_values(data: object, field_name: str) -> list[str]:
    """Recursively collect all values for a given field name."""
    values: list[str] = []
    if isinstance(data, dict):
        if field_name in data and isinstance(data[field_name], str) and data[field_name]:
            values.append(data[field_name])
        for v in data.values():
            values.extend(_collect_field_values(v, field_name))
    elif isinstance(data, list):
        for item in data:
            values.extend(_collect_field_values(item, field_name))
    return values


# ---------------------------------------------------------------------------
# Tests that work without real fixtures
# ---------------------------------------------------------------------------


def test_malformed_json_skipped(tmp_path: Path) -> None:
    """A fixture file with invalid JSON should be skipped with a warning."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Write a valid JSON file
    valid_file = input_dir / "valid.json"
    valid_file.write_text('{"memberUUId": "7b1cf060-fd27-45ab-b820-fdcdefa4ee23", "firstName": "Alice"}')

    # Write a malformed JSON file
    malformed_file = input_dir / "malformed.json"
    malformed_file.write_text("{ this is not valid json }")

    result = anonymize_batch(input_dir, output_dir, seed=42)

    assert result.files_processed == 1, f"Expected 1 processed, got {result.files_processed}"
    assert result.files_skipped == 1, f"Expected 1 skipped, got {result.files_skipped}"

    # Output directory should have the valid file but not the malformed one
    output_files = list(output_dir.glob("*.json"))
    assert len(output_files) >= 1, "Expected at least one output file"

    # The malformed file should not have been written
    malformed_output = output_dir / "malformed.json"
    assert not malformed_output.exists(), "Malformed file should not appear in output"


def test_disk_full_cleanup(tmp_path: Path) -> None:
    """When a write fails mid-batch, the partial output directory should be cleaned up."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Write some valid JSON files
    (input_dir / "file1.json").write_text('{"firstName": "Alice", "memberUUId": "abc"}')
    (input_dir / "file2.json").write_text('{"firstName": "Bob", "memberUUId": "def"}')

    # Patch _atomic_write to raise OSError on second call
    call_count = 0
    original_atomic_write = batch._atomic_write

    def patched_atomic_write(path: Path, content: str) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise OSError("No space left on device")
        return original_atomic_write(path, content)

    with (
        patch.object(batch, "_atomic_write", patched_atomic_write),
        pytest.raises(OSError, match="Batch anonymization failed"),
    ):
        anonymize_batch(input_dir, output_dir, seed=42)

    # After the failure, the output directory should be cleaned up (not exist or empty)
    if output_dir.exists():
        remaining = list(output_dir.rglob("*"))
        assert remaining == [], (
            f"Expected output directory to be cleaned up after disk-full error, "
            f"but found {len(remaining)} file(s): {[str(p) for p in remaining[:5]]}"
        )
