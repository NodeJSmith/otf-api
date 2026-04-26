"""Tests for Faker-backed PII generators."""

import re
import uuid

import pytest

from otf_api.anonymize.generators import FakeDataGenerators


@pytest.fixture
def gen() -> FakeDataGenerators:
    """Seeded generator instance for deterministic test output."""
    return FakeDataGenerators(seed=42)


def test_fake_uuid_format(gen: FakeDataGenerators) -> None:
    """fake_uuid() must return a valid UUID4 string."""
    result = gen.fake_uuid()
    # Must be parseable as a UUID
    parsed = uuid.UUID(result)
    assert parsed.version == 4


def test_fake_email_format(gen: FakeDataGenerators) -> None:
    """fake_email() must contain '@' and a domain with a '.'."""
    result = gen.fake_email()
    assert "@" in result
    domain_part = result.split("@")[1]
    assert "." in domain_part


def test_fake_phone_format(gen: FakeDataGenerators) -> None:
    """fake_phone() must return a 10-digit string (digits only)."""
    result = gen.fake_phone()
    digits_only = re.sub(r"\D", "", result)
    assert len(digits_only) == 10, f"Expected 10 digits, got {len(digits_only)}: {result!r}"


def test_fake_biometric_weight_in_range(gen: FakeDataGenerators) -> None:
    """fake_biometric_scalar('weight') must return a value in a realistic human range (lbs)."""
    result = gen.fake_biometric_scalar("weight", 150.0)
    assert isinstance(result, float)
    # 60-500 lbs is the realistic human range
    assert 60.0 <= result <= 500.0, f"Weight {result} out of range"


def test_fake_biometric_height_in_range(gen: FakeDataGenerators) -> None:
    """fake_biometric_scalar('height') must return a realistic height in cm."""
    result = gen.fake_biometric_scalar("height", 170.0)
    assert isinstance(result, float)
    # 100-250 cm
    assert 100.0 <= result <= 250.0, f"Height {result} out of range"


def test_fake_biometric_max_hr_in_range(gen: FakeDataGenerators) -> None:
    """fake_biometric_scalar('maxHr') must return a realistic HR (bpm)."""
    result = gen.fake_biometric_scalar("maxHr", 180.0)
    assert isinstance(result, float)
    # 100-220 bpm
    assert 100.0 <= result <= 220.0, f"maxHr {result} out of range"


def test_fake_biometric_age_in_range(gen: FakeDataGenerators) -> None:
    """fake_biometric_scalar('age') must return an integer-like value in a realistic age range."""
    result = gen.fake_biometric_scalar("age", 35.0)
    assert isinstance(result, float)
    # 18-90 years
    assert 18.0 <= result <= 90.0, f"Age {result} out of range"


def test_seeded_determinism() -> None:
    """Same seed must produce identical output for all generator methods."""
    gen1 = FakeDataGenerators(seed=123)
    gen2 = FakeDataGenerators(seed=123)

    assert gen1.fake_uuid() == gen2.fake_uuid()
    assert gen1.fake_email() == gen2.fake_email()
    assert gen1.fake_phone() == gen2.fake_phone()
    assert gen1.fake_biometric_scalar("weight", 150.0) == gen2.fake_biometric_scalar("weight", 150.0)
    assert gen1.fake_name() == gen2.fake_name()
    assert gen1.fake_image_url() == gen2.fake_image_url()


def test_different_seeds_differ() -> None:
    """Different seeds must produce different UUIDs (overwhelmingly likely)."""
    gen1 = FakeDataGenerators(seed=1)
    gen2 = FakeDataGenerators(seed=2)
    assert gen1.fake_uuid() != gen2.fake_uuid()


def test_fake_numeric_id_returns_int(gen: FakeDataGenerators) -> None:
    """fake_numeric_id() must return an integer."""
    result = gen.fake_numeric_id()
    assert isinstance(result, int)
    assert result > 0


def test_fake_name_returns_string(gen: FakeDataGenerators) -> None:
    """fake_name() must return a non-empty string."""
    result = gen.fake_name()
    assert isinstance(result, str)
    assert len(result) > 0


def test_fake_address_components_returns_dict(gen: FakeDataGenerators) -> None:
    """fake_address_components() must return a dict with expected address keys."""
    result = gen.fake_address_components()
    assert isinstance(result, dict)
    for key in ("address1", "city", "state", "postalCode", "country"):
        assert key in result, f"Missing key {key!r} in address components"


def test_fake_birthday_format(gen: FakeDataGenerators) -> None:
    """fake_birthday() must return a date string in YYYY-MM-DD format."""
    result = gen.fake_birthday()
    assert isinstance(result, str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", result), f"Birthday {result!r} not in YYYY-MM-DD format"


def test_fake_cc_last4_format(gen: FakeDataGenerators) -> None:
    """fake_cc_last4() must return a 4-digit string."""
    result = gen.fake_cc_last4()
    assert isinstance(result, str)
    assert re.match(r"^\d{4}$", result), f"CC last4 {result!r} is not 4 digits"


def test_fake_price_positive(gen: FakeDataGenerators) -> None:
    """fake_price() must return a non-negative float."""
    result = gen.fake_price()
    assert isinstance(result, float)
    assert result >= 0.0


def test_fake_body_comp_factor_in_range(gen: FakeDataGenerators) -> None:
    """fake_body_comp_factor() must return a float scale factor in (0, 2]."""
    result = gen.fake_body_comp_factor()
    assert isinstance(result, float)
    assert 0.0 < result <= 2.0, f"Body comp factor {result} out of range"


def test_fake_hr_delta_is_int(gen: FakeDataGenerators) -> None:
    """fake_hr_delta() must return an integer offset for HR values."""
    result = gen.fake_hr_delta()
    assert isinstance(result, int)


def test_fake_timestamp_delta_is_int(gen: FakeDataGenerators) -> None:
    """fake_timestamp_delta() must return an integer (seconds offset)."""
    result = gen.fake_timestamp_delta()
    assert isinstance(result, int)


def test_fake_image_url_format(gen: FakeDataGenerators) -> None:
    """fake_image_url() must return a string that looks like a URL."""
    result = gen.fake_image_url()
    assert isinstance(result, str)
    assert result.startswith("https://"), f"Image URL {result!r} does not start with 'https://'"
