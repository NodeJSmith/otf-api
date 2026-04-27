"""Top-level pytest configuration and shared test utilities."""

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "anonymized"

MOCK_MEMBER_UUID = "bdd640fb-0667-4ad1-9c80-317fa3b1799d"
MOCK_COGNITO_ID = "23b8c1e9-3924-46de-beb1-3b9046685257"


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
