"""Tests for the PII validator (WP04)."""

import pytest

from otf_api.anonymize.mappings import FIELD_MAPPINGS
from otf_api.anonymize.validator import (
    LeakReport,
    PiiValidator,
    ValidationResult,
    collect_real_values,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def real_name() -> str:
    """A real first name used as a known PII value in tests."""
    return "Jessica"


@pytest.fixture
def real_email() -> str:
    """A real email address used as a known PII value in tests."""
    return "jessica@example.com"


@pytest.fixture
def real_uuid() -> str:
    """A real UUID used as a known PII value in tests."""
    return "7b1cf060-fd27-45ab-b820-fdcdefa4ee23"


@pytest.fixture
def validator(real_name: str, real_email: str, real_uuid: str) -> PiiValidator:
    """Validator seeded with a few known real values."""
    return PiiValidator(known_real_values={real_name, real_email, real_uuid})


# ---------------------------------------------------------------------------
# ValidationResult / LeakReport dataclass smoke tests
# ---------------------------------------------------------------------------


def test_validation_result_defaults() -> None:
    """ValidationResult defaults are correctly initialised."""
    result = ValidationResult(passed=True, leaks=[], structural_errors=[], model_parse_errors=[])
    assert result.passed is True
    assert result.leaks == []
    assert result.structural_errors == []
    assert result.model_parse_errors == []


def test_leak_report_fields() -> None:
    """LeakReport stores all expected fields."""
    report = LeakReport(file="foo.json", field_path="data.firstName", real_value="Jessica", category="name")
    assert report.file == "foo.json"
    assert report.field_path == "data.firstName"
    assert report.real_value == "Jessica"
    assert report.category == "name"


# ---------------------------------------------------------------------------
# test_catches_leaked_name
# ---------------------------------------------------------------------------


def test_catches_leaked_name(validator: PiiValidator, real_name: str) -> None:
    """Inject a real name into anonymized output — validator must flag it."""
    original = {"data": {"firstName": real_name, "email": "old@old.com"}}
    anonymized = {"data": {"firstName": real_name, "email": "anon@fake.com"}}  # leak: name not replaced

    result = validator.validate_file(original, anonymized, "member_detail.json")

    assert not result.passed
    leak_values = [lr.real_value for lr in result.leaks]
    assert real_name in leak_values


# ---------------------------------------------------------------------------
# test_catches_leaked_email
# ---------------------------------------------------------------------------


def test_catches_leaked_email(validator: PiiValidator, real_email: str) -> None:
    """Inject a real email into anonymized output — validator must flag it."""
    original = {"email": real_email}
    anonymized = {"email": real_email}  # not replaced

    result = validator.validate_file(original, anonymized, "member.json")

    assert not result.passed
    leak_values = [lr.real_value for lr in result.leaks]
    assert real_email in leak_values


# ---------------------------------------------------------------------------
# test_catches_leaked_uuid
# ---------------------------------------------------------------------------


def test_catches_leaked_uuid(validator: PiiValidator, real_uuid: str) -> None:
    """Inject a real UUID into anonymized output — validator must flag it."""
    original = {"memberUUId": real_uuid}
    anonymized = {"memberUUId": real_uuid}  # not replaced

    result = validator.validate_file(original, anonymized, "member.json")

    assert not result.passed
    leak_values = [lr.real_value for lr in result.leaks]
    assert real_uuid in leak_values


# ---------------------------------------------------------------------------
# test_catches_leak_in_filename
# ---------------------------------------------------------------------------


def test_catches_leak_in_filename(real_uuid: str) -> None:
    """A real UUID embedded in a filename must be flagged."""
    validator = PiiValidator(known_real_values={real_uuid})
    original = {"someField": "value"}
    anonymized = {"someField": "value"}
    filename = f"member--members--{real_uuid}.json"  # UUID in filename, not replaced

    result = validator.validate_file(original, anonymized, filename)

    assert not result.passed
    leak_values = [lr.real_value for lr in result.leaks]
    assert real_uuid in leak_values


# ---------------------------------------------------------------------------
# test_passes_clean_output
# ---------------------------------------------------------------------------


def test_passes_clean_output(validator: PiiValidator) -> None:
    """Fully anonymized data with no real values passes validation."""
    original = {"firstName": "Jessica", "email": "jessica@example.com"}
    anonymized = {"firstName": "Alice", "email": "alice@fakefake.com"}

    result = validator.validate_file(original, anonymized, "clean.json")

    assert result.passed
    assert result.leaks == []
    assert result.structural_errors == []


# ---------------------------------------------------------------------------
# test_structural_mismatch_missing_key
# ---------------------------------------------------------------------------


def test_structural_mismatch_missing_key() -> None:
    """Removing a key from anonymized output is flagged as a structural error."""
    validator = PiiValidator(known_real_values=set())
    original = {"firstName": "Alice", "lastName": "Smith"}
    anonymized = {"firstName": "Bob"}  # lastName removed

    result = validator.validate_file(original, anonymized, "partial.json")

    assert not result.passed
    assert result.structural_errors  # at least one error


# ---------------------------------------------------------------------------
# test_structural_mismatch_type_change
# ---------------------------------------------------------------------------


def test_structural_mismatch_type_change() -> None:
    """Changing a string to int in anonymized output is flagged."""
    validator = PiiValidator(known_real_values=set())
    original = {"count": "5"}
    anonymized = {"count": 5}  # type changed from str to int

    result = validator.validate_file(original, anonymized, "type_change.json")

    assert not result.passed
    assert result.structural_errors


# ---------------------------------------------------------------------------
# test_null_preservation_check
# ---------------------------------------------------------------------------


def test_null_preservation_check() -> None:
    """Non-null where original was null must be flagged, and vice versa."""
    validator = PiiValidator(known_real_values=set())

    # Original null replaced with a value
    original = {"field": None}
    anonymized = {"field": "unexpected_value"}
    result = validator.validate_file(original, anonymized, "null_test.json")
    assert not result.passed
    assert result.structural_errors

    # Original non-null replaced with null
    original2 = {"field": "some_value"}
    anonymized2 = {"field": None}
    result2 = validator.validate_file(original2, anonymized2, "null_test2.json")
    assert not result2.passed
    assert result2.structural_errors


# ---------------------------------------------------------------------------
# test_collect_real_values_includes_variants
# ---------------------------------------------------------------------------


def test_collect_real_values_includes_variants() -> None:
    """Email collected in both '@' and '%40' forms."""
    email = "user@example.com"
    data = {"email": email, "firstName": "Alice"}

    # Use the email FieldMapping
    email_mapping = next(m for m in FIELD_MAPPINGS if m.category == "email")
    values = collect_real_values(data, [email_mapping])

    assert email in values
    assert "user%40example.com" in values


# ---------------------------------------------------------------------------
# test_case_insensitive_leak_detection
# ---------------------------------------------------------------------------


def test_case_insensitive_leak_detection() -> None:
    """'Jessica' detected even when output contains 'jessica' (lowercase)."""
    validator = PiiValidator(known_real_values={"Jessica"})
    original = {"firstName": "Jessica"}
    anonymized = {"firstName": "jessica"}  # same value, different case — still a leak

    result = validator.validate_file(original, anonymized, "case_test.json")

    assert not result.passed
    leak_values = [lr.real_value for lr in result.leaks]
    assert "Jessica" in leak_values
