"""Faker-backed generators for each PII category.

All generators are seeded for reproducibility.  Instantiate with a fixed seed
to get deterministic output; omit the seed (or pass ``None``) for random output.
"""

import random
import threading
import uuid

from faker import Faker

# Realistic ranges for biometric scalar fields.
_BIOMETRIC_RANGES: dict[str, tuple[float, float]] = {
    # Weight in pounds
    "weight": (60.0, 500.0),
    # Height in centimeters
    "height": (100.0, 250.0),
    # Heart-rate fields in bpm
    "maxHr": (100.0, 220.0),
    "automatedHr": (100.0, 220.0),
    "formulaMaxHr": (100.0, 220.0),
    "manualMaxHr": (100.0, 220.0),
    # Age in years
    "age": (18.0, 90.0),
}

# Possible gender values (non-PII replacement pool for the gender field).
_GENDER_VALUES: tuple[str, ...] = ("M", "F")


class FakeDataGenerators:
    """Seeded fake-data generators for every PII category.

    Args:
        seed: Integer seed for deterministic output.  Pass ``None`` for random.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._faker = Faker()
        # seed_instance() seeds only this Faker instance, not the class-level
        # shared state — required for per-instance determinism.
        self._faker.seed_instance(seed)
        self._rng = random.Random(seed)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def fake_uuid(self) -> str:
        """Return a valid UUID4 string."""
        with self._lock:
            return str(uuid.UUID(int=self._rng.getrandbits(128), version=4))

    def fake_numeric_id(self) -> int:
        """Return a positive random integer suitable for a numeric member/studio ID."""
        with self._lock:
            return self._rng.randint(100_000, 999_999_999)

    # ------------------------------------------------------------------
    # Personal info
    # ------------------------------------------------------------------

    def fake_first_name(self) -> str:
        """Return a fake first name."""
        with self._lock:
            return self._faker.first_name()

    def fake_last_name(self) -> str:
        """Return a fake last name."""
        with self._lock:
            return self._faker.last_name()

    def fake_email(self) -> str:
        """Return a fake email address."""
        with self._lock:
            return self._faker.email()

    def fake_phone(self) -> str:
        """Return a 10-digit US phone number string (digits only)."""
        with self._lock:
            area = self._rng.randint(200, 999)
            exchange = self._rng.randint(200, 999)
            subscriber = self._rng.randint(0, 9999)
            return f"{area:03d}{exchange:03d}{subscriber:04d}"

    def fake_address_components(self) -> dict[str, str]:
        """Return a dict of fake address components keyed by JSON field names."""
        with self._lock:
            return {
                "address1": self._faker.street_address(),
                "city": self._faker.city(),
                "state": self._faker.state_abbr(),
                "postalCode": self._faker.postcode(),
                "country": self._faker.country_code(representation="alpha-2"),
            }

    def fake_birthday(self) -> str:
        """Return a fake birthday in YYYY-MM-DD format for a plausible adult age."""
        with self._lock:
            dob = self._faker.date_of_birth(minimum_age=18, maximum_age=90)
            return dob.isoformat()

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------

    def fake_cc_last4(self) -> str:
        """Return a fake 4-digit credit card suffix."""
        with self._lock:
            return f"{self._rng.randint(0, 9999):04d}"

    def fake_price(self) -> float:
        """Return a non-negative fake price."""
        with self._lock:
            return round(self._rng.uniform(0.0, 500.0), 2)

    def fake_cc_type(self) -> str:
        """Return a fake credit card brand name."""
        with self._lock:
            return self._rng.choice(("Visa", "Master Card", "American Express", "Discover"))

    def fake_gender(self) -> str:
        """Return a random gender value from the known API values."""
        with self._lock:
            return self._rng.choice(_GENDER_VALUES)

    # ------------------------------------------------------------------
    # Biometric
    # ------------------------------------------------------------------

    def fake_biometric_scalar(self, field_name: str, _original_value: float) -> float:
        """Return a fake biometric scalar value in the realistic human range for the field.

        Args:
            field_name: JSON key of the biometric field (used to select the range).
            _original_value: Original value (reserved for future format-preserving
                strategies; not used in current implementation).

        Returns:
            A float within the realistic range for the given field.
        """
        lo, hi = _BIOMETRIC_RANGES.get(field_name, (0.0, 1000.0))
        with self._lock:
            return round(self._rng.uniform(lo, hi), 2)

    def fake_body_comp_factor(self) -> float:
        """Return a scale factor in (0, 2] for body composition values.

        Apply this factor uniformly to all body comp fields for a single scan
        to preserve the internal ratios of the measurement.
        """
        with self._lock:
            return round(self._rng.uniform(0.5, 1.5), 4)

    def fake_hr_delta(self) -> int:
        """Return an integer HR offset (bpm) for telemetry anonymization.

        Apply this delta uniformly to all HR values in a single workout to
        preserve the relative HR profile while shifting absolute values.
        """
        with self._lock:
            return self._rng.randint(-30, 30)

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    def fake_timestamp_delta(self) -> int:
        """Return an integer seconds offset for timestamp anonymization.

        Apply this delta uniformly to all timestamps in a single session to
        preserve relative ordering while shifting absolute dates.
        Range: ±365 days expressed in seconds.
        """
        with self._lock:
            return self._rng.randint(-365 * 24 * 3600, 365 * 24 * 3600)

    # ------------------------------------------------------------------
    # Studio / Geo
    # ------------------------------------------------------------------

    def fake_studio_name(self) -> str:
        """Return a fake studio name in OTF's 'City - Direction, ST' format."""
        with self._lock:
            city = self._faker.city()
            direction = self._rng.choice(("East", "West", "North", "South", "Central", "Downtown"))
            state = self._faker.state_abbr()
            return f"{city} - {direction}, {state}"

    def fake_geo_coordinate(self, original: float) -> float:
        """Return a fake coordinate offset from the original by a random amount.

        Clamps to valid WGS-84 ranges: [-90, 90] for latitude, [-180, 180] for longitude.
        """
        with self._lock:
            fake = round(original + self._rng.uniform(-5.0, 5.0), 6)
        if abs(original) <= 90:
            return max(-90.0, min(90.0, fake))
        return max(-180.0, min(180.0, fake))

    # ------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------

    def fake_image_url(self) -> str:
        """Return a placeholder image URL."""
        with self._lock:
            return f"https://placeholder.example.com/profile/{self._rng.randint(1, 999_999)}.jpg"
