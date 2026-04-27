"""Top-level pytest configuration and shared test utilities."""

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "anonymized"

MOCK_MEMBER_UUID = "b1ef4b6c-3045-49fd-a21b-7244f6692002"
MOCK_COGNITO_ID = "aefb4ee1-e56d-4d97-8cde-9a7260a514e4"


def load_fixture(name: str) -> dict | list:
    """Load and parse a fixture JSON file by name (relative to fixtures/anonymized/).

    Args:
        name: Fixture filename without extension, e.g. ``"members/get_member_detail"``.

    Returns:
        Parsed JSON content as a dict or list.
    """
    path = FIXTURE_DIR / f"{name}.json"
    return json.loads(path.read_text())


FIXTURE_INDEX: list[dict] = load_fixture("index")
