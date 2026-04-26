"""Tests for AnonymizedCaptureHook and create_capture_hook factory."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer
from otf_api.anonymize.generators import FakeDataGenerators
from otf_api.anonymize.hooks import AnonymizedCaptureHook, create_capture_hook
from otf_api.anonymize.mappings import FIELD_MAPPINGS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_anonymizer(seed: int = 42, strictness: str = "permissive") -> Anonymizer:
    config = AnonymizeConfig(seed=seed, strictness=strictness)  # type: ignore[arg-type]
    generators = FakeDataGenerators(seed=seed)
    return Anonymizer(config=config, generators=generators, mappings=FIELD_MAPPINGS)


def _make_json_response(
    body: dict | list,
    url: str = "https://api.orangetheory.co/v1/members/abc-123/profile",
    method: str = "GET",
    status_code: int = 200,
) -> httpx.Response:
    """Build a mock httpx.Response with JSON content."""
    body_bytes = json.dumps(body).encode("utf-8")
    request = httpx.Request(method, url)
    response = httpx.Response(
        status_code=status_code,
        content=body_bytes,
        headers={"content-type": "application/json"},
        request=request,
    )
    return response


def _make_non_json_response(
    url: str = "https://api.orangetheory.co/v1/health",
    method: str = "GET",
) -> httpx.Response:
    """Build a mock httpx.Response with plain-text content that is not JSON."""
    request = httpx.Request(method, url)
    return httpx.Response(
        status_code=200,
        content=b"OK",
        headers={"content-type": "text/plain"},
        request=request,
    )


# ---------------------------------------------------------------------------
# test_hook_writes_anonymized_output
# ---------------------------------------------------------------------------


def test_hook_writes_anonymized_output(tmp_path: Path) -> None:
    """Hook writes anonymized JSON to the output directory."""
    anonymizer = _make_anonymizer(seed=1)
    hook = AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=tmp_path)

    body = {
        "memberUUId": "real-uuid-1234-5678-9012-345678901234",
        "firstName": "RealFirst",
        "lastName": "RealLast",
        "email": "real@example.com",
        "status": "Active",
    }
    response = _make_json_response(body)
    hook(response)

    # The host directory should have been created
    host_dir = tmp_path / "api.orangetheory.co"
    assert host_dir.is_dir()

    # At least one .json file should exist under the host dir
    output_files = list(host_dir.glob("*.json"))
    assert len(output_files) == 1

    written = json.loads(output_files[0].read_text())

    # URL should be present
    assert "url" in written
    assert "body" in written

    # Real PII must not appear in the serialized output
    text = output_files[0].read_text()
    assert "RealFirst" not in text
    assert "RealLast" not in text
    assert "real@example.com" not in text


# ---------------------------------------------------------------------------
# test_hook_handles_non_json_response
# ---------------------------------------------------------------------------


def test_hook_handles_non_json_response(tmp_path: Path) -> None:
    """Hook skips non-JSON responses without raising."""
    anonymizer = _make_anonymizer(seed=2)
    hook = AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=tmp_path)

    response = _make_non_json_response()

    # Must not raise
    hook(response)

    # No capture files should be written for a skipped response (only the
    # capture-start sentinel may exist).
    host_dir = tmp_path / "api.orangetheory.co"
    assert not host_dir.exists() or list(host_dir.glob("*.json")) == []


# ---------------------------------------------------------------------------
# test_hook_error_does_not_propagate
# ---------------------------------------------------------------------------


def test_hook_error_does_not_propagate(tmp_path: Path) -> None:
    """If the anonymizer raises, the hook catches and logs — does not re-raise."""
    anonymizer = _make_anonymizer(seed=3)
    # Patch anonymize_dict to raise
    anonymizer.anonymize_dict = MagicMock(side_effect=RuntimeError("boom"))

    hook = AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=tmp_path)

    body = {"someField": "someValue"}
    response = _make_json_response(body)

    # Must not raise
    hook(response)


# ---------------------------------------------------------------------------
# test_capture_start_json_written
# ---------------------------------------------------------------------------


def test_capture_start_json_written(tmp_path: Path) -> None:
    """First hook invocation writes _capture_start.json to the output directory."""
    anonymizer = _make_anonymizer(seed=4)
    hook = AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=tmp_path)

    body = {"status": "ok"}
    response = _make_json_response(body)
    hook(response)

    sentinel = tmp_path / "_capture_start.json"
    assert sentinel.exists(), "_capture_start.json should be written on first call"

    data = json.loads(sentinel.read_text())
    assert "timestamp" in data
    assert "output_dir" in data
    assert "strictness" in data


def test_capture_start_json_written_only_once(tmp_path: Path) -> None:
    """Subsequent hook calls do not overwrite _capture_start.json."""
    anonymizer = _make_anonymizer(seed=5)
    hook = AnonymizedCaptureHook(anonymizer=anonymizer, output_dir=tmp_path)

    body = {"status": "ok"}
    response1 = _make_json_response(body, url="https://api.orangetheory.co/v1/a")
    response2 = _make_json_response(body, url="https://api.orangetheory.co/v1/b")

    hook(response1)
    sentinel = tmp_path / "_capture_start.json"
    mtime_after_first = sentinel.stat().st_mtime

    hook(response2)
    mtime_after_second = sentinel.stat().st_mtime

    assert mtime_after_first == mtime_after_second, "_capture_start.json must not be overwritten"


# ---------------------------------------------------------------------------
# test_env_var_config_parsing
# ---------------------------------------------------------------------------


def test_env_var_config_parsing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """create_capture_hook reads all 4 env vars correctly."""
    monkeypatch.setenv("OTF_ANONYMIZE_RESPONSES", "true")
    monkeypatch.setenv("OTF_ANONYMIZE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("OTF_ANONYMIZE_SEED", "99")
    monkeypatch.setenv("OTF_ANONYMIZE_STRICTNESS", "mask")

    hook = create_capture_hook()

    assert hook.output_dir == tmp_path
    assert hook.anonymizer._config.seed == 99
    assert hook.anonymizer._config.strictness == "mask"


def test_env_var_config_parsing_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_capture_hook uses permissive strictness and random seed when vars are unset."""
    monkeypatch.delenv("OTF_ANONYMIZE_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("OTF_ANONYMIZE_SEED", raising=False)
    monkeypatch.delenv("OTF_ANONYMIZE_STRICTNESS", raising=False)

    hook = create_capture_hook()

    assert hook.anonymizer._config.strictness == "permissive"
    assert hook.anonymizer._config.seed is None


def test_env_var_invalid_strictness_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid OTF_ANONYMIZE_STRICTNESS falls back to permissive without raising."""
    monkeypatch.setenv("OTF_ANONYMIZE_STRICTNESS", "invalid_value")
    monkeypatch.delenv("OTF_ANONYMIZE_SEED", raising=False)
    monkeypatch.delenv("OTF_ANONYMIZE_OUTPUT_DIR", raising=False)

    hook = create_capture_hook()

    assert hook.anonymizer._config.strictness == "permissive"


def test_env_var_invalid_seed_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid OTF_ANONYMIZE_SEED falls back to None seed without raising."""
    monkeypatch.setenv("OTF_ANONYMIZE_SEED", "not-an-int")
    monkeypatch.delenv("OTF_ANONYMIZE_STRICTNESS", raising=False)
    monkeypatch.delenv("OTF_ANONYMIZE_OUTPUT_DIR", raising=False)

    hook = create_capture_hook()

    assert hook.anonymizer._config.seed is None


def test_create_capture_hook_uses_provided_config(tmp_path: Path) -> None:
    """create_capture_hook uses a provided AnonymizeConfig, ignoring env vars."""
    config = AnonymizeConfig(seed=777, strictness="drop", output_dir=tmp_path)

    hook = create_capture_hook(config=config)

    assert hook.anonymizer._config.seed == 777
    assert hook.anonymizer._config.strictness == "drop"
    assert hook.output_dir == tmp_path
