"""Tests for domain-specific anonymization transforms (WP03).

Covers:
- Body composition scaling (preserving mathematical relationships between ~50 fields)
- Heart rate telemetry offsetting (recalculating zone boundaries from anonymized maxHr)
- Address format correlation (ensuring different text representations of the same
  physical address map to the same fake address)
"""

import pytest

from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer
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
    """Permissive config with fixed seed."""
    return AnonymizeConfig(seed=42, strictness="permissive")


@pytest.fixture
def anonymizer(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> Anonymizer:
    """Anonymizer with seeded generators and permissive config."""
    return Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)


def _make_body_comp_scan(tbw: float = 40.0, bfm: float = 15.0, lbm: float = 25.0) -> dict:
    """Return a minimal body comp scan dict with required detection fields."""
    return {
        "tbw": tbw,
        "bfm": bfm,
        "lbm": lbm,
        "smm": 14.0,
        "bmr": 1500.0,
        "bmi": 22.0,
        "pbf": round(bfm / (bfm + lbm) * 100, 2),
    }


def _make_telemetry_array(hr_values: list[int]) -> list[dict]:
    """Return a minimal telemetry array."""
    return [{"hr": hr, "relativeTimestamp": i * 10} for i, hr in enumerate(hr_values)]


def _make_workout_with_telemetry(hr_values: list[int], max_hr: int = 185) -> dict:
    """Return a workout dict with telemetry and zone structure."""
    telemetry = _make_telemetry_array(hr_values)
    return {
        "workoutUUId": "workout-uuid-1234",
        "maxHr": max_hr,
        "telemetry": telemetry,
        "zones": {
            "gray": {"startBpm": 0, "endBpm": round(max_hr * 0.62)},
            "blue": {"startBpm": round(max_hr * 0.62), "endBpm": round(max_hr * 0.72)},
            "green": {"startBpm": round(max_hr * 0.72), "endBpm": round(max_hr * 0.84)},
            "orange": {"startBpm": round(max_hr * 0.84), "endBpm": round(max_hr * 0.92)},
            "red": {"startBpm": round(max_hr * 0.92), "endBpm": max_hr},
        },
    }


# ---------------------------------------------------------------------------
# Body composition scaling
# ---------------------------------------------------------------------------


def test_body_comp_scaling_preserves_ratios(anonymizer: Anonymizer) -> None:
    """After scaling, lean mass + fat mass ≈ tbw (total body weight-related water components).

    More precisely: the ratio bfm/lbm should be preserved before and after anonymization.
    """
    bfm = 20.0
    lbm = 60.0
    scan = _make_body_comp_scan(tbw=38.0, bfm=bfm, lbm=lbm)
    result = anonymizer.anonymize_dict(scan)

    orig_ratio = bfm / lbm
    anon_ratio = result["bfm"] / result["lbm"]
    assert abs(orig_ratio - anon_ratio) < 0.001, (
        f"bfm/lbm ratio changed: original={orig_ratio:.4f}, anonymized={anon_ratio:.4f}"
    )


def test_body_comp_consistent_factor_per_scan(anonymizer: Anonymizer) -> None:
    """All fields in a single body comp scan are scaled by the same factor."""
    tbw = 40.0
    bfm = 15.0
    lbm = 25.0
    smm = 14.0
    scan = _make_body_comp_scan(tbw=tbw, bfm=bfm, lbm=lbm)
    scan["smm"] = smm
    result = anonymizer.anonymize_dict(scan)

    # Derive the factor from tbw
    factor = result["tbw"] / tbw
    # All other fields should use the same factor
    assert abs(result["bfm"] / bfm - factor) < 0.001
    assert abs(result["lbm"] / lbm - factor) < 0.001
    assert abs(result["smm"] / smm - factor) < 0.001


def test_body_comp_different_factor_per_scan(
    config_permissive: AnonymizeConfig, generators: FakeDataGenerators
) -> None:
    """Two different scan objects get different scaling factors."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)

    scan1 = _make_body_comp_scan(tbw=40.0, bfm=15.0, lbm=25.0)
    scan2 = _make_body_comp_scan(tbw=45.0, bfm=18.0, lbm=27.0)

    result1 = anon.anonymize_dict(scan1)
    result2 = anon.anonymize_dict(scan2)

    factor1 = result1["tbw"] / 40.0
    factor2 = result2["tbw"] / 45.0

    assert abs(factor1 - factor2) > 0.001, f"Both scans got the same factor {factor1:.4f}, expected different factors"


# ---------------------------------------------------------------------------
# Heart-rate telemetry
# ---------------------------------------------------------------------------


def test_hr_zone_recalculation(anonymizer: Anonymizer) -> None:
    """Zone startBpm/endBpm are derived from the anonymized maxHr, not the original."""
    max_hr = 185
    workout = _make_workout_with_telemetry([150, 160, 170], max_hr=max_hr)
    result = anonymizer.anonymize_dict(workout)

    anon_max_hr = result["maxHr"]
    # maxHr is a biometric_scalar — it should be changed
    assert anon_max_hr != max_hr

    # Zone boundaries must be derived from the anonymized maxHr
    zones = result["zones"]
    expected_green_start = round(anon_max_hr * 0.72)
    expected_orange_start = round(anon_max_hr * 0.84)

    assert zones["green"]["startBpm"] == expected_green_start, (
        f"green.startBpm={zones['green']['startBpm']} but expected {expected_green_start} "
        f"(72% of anonymized maxHr={anon_max_hr})"
    )
    assert zones["orange"]["startBpm"] == expected_orange_start, (
        f"orange.startBpm={zones['orange']['startBpm']} but expected {expected_orange_start} "
        f"(84% of anonymized maxHr={anon_max_hr})"
    )


def test_hr_delta_consistent_per_workout(anonymizer: Anonymizer) -> None:
    """All HR values in one telemetry array are offset by the same delta."""
    hr_values = [140, 150, 160, 155]
    workout = _make_workout_with_telemetry(hr_values, max_hr=185)
    result = anonymizer.anonymize_dict(workout)

    anon_hrs = [entry["hr"] for entry in result["telemetry"]]
    # All deltas from the original HR values should be identical
    deltas = [anon - orig for anon, orig in zip(anon_hrs, hr_values, strict=True)]
    assert len(set(deltas)) == 1, f"Expected uniform HR delta, got multiple: {deltas}"


def test_hr_delta_different_per_workout(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Two different workout objects get different HR deltas."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)

    workout1 = _make_workout_with_telemetry([140, 150], max_hr=185)
    workout2 = _make_workout_with_telemetry([145, 155], max_hr=180)

    result1 = anon.anonymize_dict(workout1)
    result2 = anon.anonymize_dict(workout2)

    delta1 = result1["telemetry"][0]["hr"] - 140
    delta2 = result2["telemetry"][0]["hr"] - 145

    assert delta1 != delta2, f"Both workouts got the same HR delta ({delta1}), expected different"


# ---------------------------------------------------------------------------
# Address correlation
# ---------------------------------------------------------------------------


def test_address_correlation_same_studio(config_permissive: AnonymizeConfig, generators: FakeDataGenerators) -> None:
    """Same studio UUID with different address text variants maps to the same fake address.

    This tests the case where the same physical address appears in different
    string representations (e.g. "123 Main St" vs "123 Main Street") — both
    should produce the same fake address because they share a studioUUId.
    """
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)

    studio_uuid = "studio-uuid-abc123"
    # Two dicts with same studio but different address strings (format variants)
    studio1 = {
        "studioUUId": studio_uuid,
        "address1": "123 Main St",
        "city": "Austin",
    }
    studio2 = {
        "studioUUId": studio_uuid,
        "address1": "123 Main Street",  # different text, same physical address
        "city": "Austin, TX",  # different city format
    }

    result1 = anon.anonymize_dict(studio1)
    result2 = anon.anonymize_dict(studio2)

    # Different string representations tied to the same studio UUID must produce
    # the same fake address components
    assert result1["address1"] == result2["address1"], (
        f"Same studio UUID produced different address1: {result1['address1']!r} vs {result2['address1']!r}"
    )


def test_address_correlation_no_identifier_fallback(
    config_permissive: AnonymizeConfig, generators: FakeDataGenerators
) -> None:
    """Without a parent identifier, address falls back to exact string matching."""
    anon = Anonymizer(config=config_permissive, generators=generators, mappings=FIELD_MAPPINGS)

    # Two separate dicts with the same address but no studio UUID
    addr_dict1 = {"address1": "456 Oak Ave", "city": "Denver"}
    addr_dict2 = {"address1": "456 Oak Ave", "city": "Denver"}

    result1 = anon.anonymize_dict(addr_dict1)
    result2 = anon.anonymize_dict(addr_dict2)

    # Same real address string → same fake address (via replacement map)
    assert result1["address1"] == result2["address1"], (
        f"Same address1 string without identifier produced different fakes: "
        f"{result1['address1']!r} vs {result2['address1']!r}"
    )
    assert result1["city"] == result2["city"], (
        f"Same city string without identifier produced different fakes: {result1['city']!r} vs {result2['city']!r}"
    )
