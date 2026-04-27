"""Tests for the core anonymizer engine (WP02)."""

import concurrent.futures
from unittest.mock import patch

import pytest

from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer, ReplacementMap
from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.mappings import FIELD_MAPPINGS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def generators() -> FakeDataGenerators:
    """Seeded generators for deterministic test output."""
    return FakeDataGenerators(seed=42)


@pytest.fixture
def config_permissive() -> AnonymizeConfig:
    """Permissive config — unknown fields pass through."""
    return AnonymizeConfig(seed=42, strictness="permissive")


@pytest.fixture
def config_mask() -> AnonymizeConfig:
    """Mask config — unknown fields get a sentinel."""
    return AnonymizeConfig(seed=42, strictness="mask")


@pytest.fixture
def config_drop() -> AnonymizeConfig:
    """Drop config — unknown fields are removed."""
    return AnonymizeConfig(seed=42, strictness="drop")


@pytest.fixture
def anonymizer(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> Anonymizer:
    """Permissive anonymizer with seeded generators."""
    return Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)


# ---------------------------------------------------------------------------
# Core replacement tests
# ---------------------------------------------------------------------------


def test_replaces_known_pii_field(anonymizer: Anonymizer) -> None:
    """A dict with firstName produces a different (fake) name."""
    result = anonymizer.anonymize_dict({"firstName": "Jessica"})
    assert "firstName" in result
    assert result["firstName"] != "Jessica"
    assert isinstance(result["firstName"], str)
    assert len(result["firstName"]) > 0


def test_preserves_null(anonymizer: Anonymizer) -> None:
    """A null PII field remains null after anonymization."""
    result = anonymizer.anonymize_dict({"workPhone": None})
    assert "workPhone" in result
    assert result["workPhone"] is None


def test_preserves_unknown_field_permissive(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown fields pass through unchanged in permissive mode."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"unknownField": "someValue"})
    assert result["unknownField"] == "someValue"


def test_masks_unknown_field_strict(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown fields get a mask sentinel in 'mask' strictness mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"unknownField": "someValue"})
    assert "unknownField" in result
    # The value should be a sentinel string, not the original
    assert result["unknownField"] != "someValue"
    assert isinstance(result["unknownField"], str)


def test_mask_mode_passes_through_int(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown int fields pass through unchanged in mask mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"classId": 42})
    assert result["classId"] == 42


def test_mask_mode_passes_through_float(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown float fields pass through unchanged in mask mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"distanceMiles": 3.14})
    assert result["distanceMiles"] == 3.14


def test_mask_mode_passes_through_bool(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown bool fields pass through unchanged in mask mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"isFinished": False})
    assert result["isFinished"] is False


def test_mask_mode_passes_through_numeric_string(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown numeric strings pass through unchanged in mask mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"year": "2026", "metricValue": "973"})
    assert result["year"] == "2026"
    assert result["metricValue"] == "973"


def test_mask_mode_passes_through_datetime_string(config_mask: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown datetime strings pass through unchanged in mask mode."""
    anon = Anonymizer(config=config_mask, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({
        "dateCreated": "2024-01-15T10:30:00Z",
        "openDate": "2016-01-22 00:00:00",
    })
    assert result["dateCreated"] == "2024-01-15T10:30:00Z"
    assert result["openDate"] == "2016-01-22 00:00:00"


def test_drops_unknown_field_strict(config_drop: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Unknown fields are removed from the output in 'drop' strictness mode."""
    anon = Anonymizer(config=config_drop, generators=generators, mappings=FIELD_MAPPINGS)
    result = anon.anonymize_dict({"unknownField": "someValue", "firstName": "Jessica"})
    # unknownField removed, but known PII field still present (anonymized)
    assert "unknownField" not in result
    assert "firstName" in result


def test_drop_mode_recurses_into_unknown_dicts(config_drop: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Drop mode recurses into unknown dict keys to find nested PII."""
    anon = Anonymizer(config=config_drop, generators=generators, mappings=FIELD_MAPPINGS)
    data = {
        "unknownWrapper": {
            "firstName": "Jessica",
            "unknownScalar": "should-be-dropped",
        }
    }
    result = anon.anonymize_dict(data)
    # The wrapper is preserved (structural unknown — must recurse for nested PII)
    assert "unknownWrapper" in result
    # Nested PII is anonymized
    assert result["unknownWrapper"]["firstName"] != "Jessica"
    # Nested scalar unknown is dropped
    assert "unknownScalar" not in result["unknownWrapper"]


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------


def test_referential_integrity_across_calls(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Same UUID in two separate anonymize_dict calls produces the same fake UUID."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    real_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    result1 = anon.anonymize_dict({"memberUUId": real_uuid})
    result2 = anon.anonymize_dict({"memberUUId": real_uuid})
    # Both calls return the same fake UUID
    assert result1["memberUUId"] == result2["memberUUId"]
    # And it's not the real value
    assert result1["memberUUId"] != real_uuid


# ---------------------------------------------------------------------------
# Recursive walk
# ---------------------------------------------------------------------------


def test_nested_dict_walk(anonymizer: Anonymizer) -> None:
    """Deeply nested structure is fully walked and all PII fields are anonymized."""
    data = {
        "code": "SUCCESS",
        "data": {
            "member": {
                "firstName": "Alice",
                "lastName": "Smith",
                "contact": {
                    "email": "alice@example.com",
                },
            }
        },
    }
    result = anonymizer.anonymize_dict(data)
    member = result["data"]["member"]
    assert member["firstName"] != "Alice"
    assert member["lastName"] != "Smith"
    assert member["contact"]["email"] != "alice@example.com"


def test_list_walk(anonymizer: Anonymizer) -> None:
    """Lists of dicts are each processed — all items have their PII replaced."""
    data = {
        "items": [
            {"firstName": "Alice", "memberId": 111111},
            {"firstName": "Bob", "memberId": 222222},
        ]
    }
    result = anonymizer.anonymize_dict(data)
    items = result["items"]
    assert items[0]["firstName"] != "Alice"
    assert items[1]["firstName"] != "Bob"
    assert items[0]["memberId"] != 111111
    assert items[1]["memberId"] != 222222


# ---------------------------------------------------------------------------
# URL and filename anonymization
# ---------------------------------------------------------------------------


def test_anonymize_url(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Member UUID in a URL path is replaced using the replacement map."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    real_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    # First, anonymize a dict to populate the replacement map
    anon.anonymize_dict({"memberUUId": real_uuid})
    url = f"/api/v1/members/{real_uuid}/bookings"
    result = anon.anonymize_url(url)
    assert real_uuid not in result
    assert "/" in result  # Structure preserved


def test_anonymize_url_query_params(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Email in a URL query parameter is replaced."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    real_email = "jessica@example.com"
    # Populate the replacement map
    anon.anonymize_dict({"email": real_email})
    url = f"/api/v1/members?email={real_email}&page=1"
    result = anon.anonymize_url(url)
    assert real_email not in result


def test_anonymize_filename(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """PII value in a fixture filename is replaced using the replacement map."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    real_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    # Populate the replacement map
    anon.anonymize_dict({"memberUUId": real_uuid})
    filename = f"member_{real_uuid}_bookings.json"
    result = anon.anonymize_filename(filename)
    assert real_uuid not in result


# ---------------------------------------------------------------------------
# Sentinel / redaction tests
# ---------------------------------------------------------------------------


def test_redacted_sentinel(anonymizer: Anonymizer) -> None:
    """StudioToken is always replaced with the 'REDACTED' sentinel."""
    result = anonymizer.anonymize_dict({"studioToken": "some-token-value-abc123"})
    assert result["studioToken"] == "REDACTED"


# ---------------------------------------------------------------------------
# ReplacementMap serialization
# ---------------------------------------------------------------------------


def test_replacement_map_serialization() -> None:
    """ReplacementMap serializes to dict and deserializes back correctly."""
    rmap = ReplacementMap()

    counter = {"n": 0}

    def gen() -> str:
        counter["n"] += 1
        return f"fake-value-{counter['n']}"

    v1 = rmap.get_or_create("real-value-a", gen)
    v2 = rmap.get_or_create("real-value-b", gen)

    serialized = rmap.to_json()
    assert isinstance(serialized, dict)

    restored = ReplacementMap.from_json(serialized)
    # After deserialization, looking up the same real values returns the same fakes
    assert restored.get_or_create("real-value-a", gen) == v1
    assert restored.get_or_create("real-value-b", gen) == v2


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


def test_replacement_map_thread_safety() -> None:
    """Concurrent access from multiple threads doesn't corrupt the replacement map."""
    rmap = ReplacementMap()
    real_value = "shared-real-value"
    results: list[str] = []
    errors: list[Exception] = []

    def worker() -> None:
        try:
            fake = rmap.get_or_create(real_value, lambda: "consistent-fake")
            results.append(fake)
        except Exception as exc:
            errors.append(exc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker) for _ in range(100)]
        concurrent.futures.wait(futures)

    assert not errors, f"Thread errors: {errors}"
    assert len(results) == 100
    # All threads must have gotten the same fake value
    assert len(set(results)) == 1, f"Expected 1 unique fake value, got: {set(results)}"


# ---------------------------------------------------------------------------
# Faker failure fallback
# ---------------------------------------------------------------------------


def test_faker_failure_fallback(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """If a generator raises, the anonymizer returns a deterministic placeholder (never the real value)."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)
    real_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    # Patch fake_uuid to raise
    with patch.object(generators, "fake_uuid", side_effect=RuntimeError("generator failure")):
        result = anon.anonymize_dict({"memberUUId": real_uuid})

    # The real value must NOT appear in output
    assert result["memberUUId"] != real_uuid
    # The placeholder must be a non-empty string
    assert isinstance(result["memberUUId"], str)
    assert len(result["memberUUId"]) > 0
