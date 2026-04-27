"""Top-level pytest configuration and shared test utilities."""

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "anonymized"

MOCK_MEMBER_UUID = "d1f6f86c-029a-4245-bb91-433a6aa79987"
MOCK_COGNITO_ID = "daea58ba-4c73-4942-8d87-78e7d340bbcd"


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
