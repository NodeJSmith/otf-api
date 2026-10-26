"""Tests for client-side security hardening."""

import stat
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from otf_api.api.trends.trend_api import TrendApi
from otf_api.api.utils import validate_identifier
from otf_api.cache import ensure_secure_directory
from otf_api.models.trends import TrendType


class TestValidateIdentifier:
    """Tests for the path segment validation helper."""

    def test_valid_uuid(self):
        result = validate_identifier("abc-123-def-456-ghi", "test")
        assert result == "abc-123-def-456-ghi"

    def test_valid_alphanumeric(self):
        result = validate_identifier("abc123", "test")
        assert result == "abc123"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_identifier("", "test_field")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("../../admin", "test_field")

    @pytest.mark.parametrize("value", [".", ".."])
    def test_rejects_relative_segment(self, value):
        with pytest.raises(ValueError, match="relative path segment"):
            validate_identifier(value, "test_field")

    def test_allows_embedded_dots(self):
        assert validate_identifier("a..b", "test") == "a..b"

    def test_rejects_slash(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("abc/def", "test_field")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("abc\\def", "test_field")

    def test_rejects_null_byte(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("abc\x00def", "test_field")

    def test_rejects_percent_encoding(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("abc%2Fdef", "test_field")

    def test_rejects_whitespace(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_identifier("abc def", "test_field")

    def test_rejects_oversized(self):
        with pytest.raises(ValueError, match="too long"):
            validate_identifier("a" * 201, "test_field")

    def test_accepts_max_length(self):
        result = validate_identifier("a" * 200, "test")
        assert len(result) == 200

    def test_error_message_includes_field_name(self):
        with pytest.raises(ValueError, match="booking_uuid"):
            validate_identifier("", "booking_uuid")


class TestEnsureSecureDirectory:
    """Tests for cache directory permission hardening."""

    def test_creates_directory_with_0700(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            ensure_secure_directory(path)
            mode = stat.S_IMODE(Path(path).stat().st_mode)
            assert mode == 0o700, f"Expected 0700, got {oct(mode)}"

    def test_tightens_existing_loose_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            Path(path).mkdir()
            Path(path).chmod(0o755)
            ensure_secure_directory(path)
            mode = stat.S_IMODE(Path(path).stat().st_mode)
            assert mode == 0o700, f"Expected 0700, got {oct(mode)}"

    def test_continues_on_chmod_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            Path(path).mkdir()
            Path(path).chmod(0o755)
            with patch("otf_api.cache.Path.chmod", side_effect=OSError("permission denied")):
                ensure_secure_directory(path)
            assert Path(path).is_dir()

    def test_skips_chmod_when_already_secure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            Path(path).mkdir()
            Path(path).chmod(0o700)
            with patch("otf_api.cache.Path.chmod") as chmod:
                ensure_secure_directory(path)
            chmod.assert_not_called()


class TestTrendTypeValidation:
    """Tests for TrendType coercion before the value reaches the URL path."""

    @staticmethod
    def _make_api() -> TrendApi:
        api = TrendApi.__new__(TrendApi)
        api.client = Mock()
        api.client.get_workout_stats.return_value = {}
        return api

    def test_accepts_enum_member(self):
        api = self._make_api()
        api.get_workout_stats(TrendType.SplatPoints)
        assert api.client.get_workout_stats.call_args.args[0] == "splat_points"

    def test_accepts_string_value(self):
        api = self._make_api()
        api.get_workout_stats("splat_points")
        assert api.client.get_workout_stats.call_args.args[0] == "splat_points"

    def test_rejects_unknown_string(self):
        api = self._make_api()
        with pytest.raises(ValueError, match="not a valid TrendType"):
            api.get_workout_stats("../preview")
        api.client.get_workout_stats.assert_not_called()
