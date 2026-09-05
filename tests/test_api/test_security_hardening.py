"""Tests for client-side security hardening."""

import os
import stat
import tempfile
from pathlib import Path

import httpx
import pytest

from otf_api.api.members.member_api import MemberApi
from otf_api.api.utils import validate_identifier
from otf_api.cache import _ensure_secure_directory
from otf_api.exceptions import OtfRequestError


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
        with pytest.raises(ValueError, match="path traversal"):
            validate_identifier("../../admin", "test_field")

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


class TestSanitizeRequest:
    """Tests for credential redaction in OtfRequestError."""

    def test_redacts_authorization_header(self):
        req = httpx.Request("GET", "https://example.com", headers={"Authorization": "Bearer secret"})
        err = OtfRequestError("test", None, None, req)
        assert err.request.headers["authorization"] == "[REDACTED]"

    def test_redacts_aws_security_token(self):
        req = httpx.Request("GET", "https://example.com", headers={"x-amz-security-token": "tok"})
        err = OtfRequestError("test", None, None, req)
        assert err.request.headers["x-amz-security-token"] == "[REDACTED]"

    def test_preserves_non_sensitive_headers(self):
        req = httpx.Request("GET", "https://example.com", headers={"content-type": "application/json"})
        err = OtfRequestError("test", None, None, req)
        assert err.request.headers["content-type"] == "application/json"

    def test_preserves_request_body(self):
        req = httpx.Request("POST", "https://example.com", content=b'{"key": "value"}')
        err = OtfRequestError("test", None, None, req)
        assert err.request.content == b'{"key": "value"}'

    def test_does_not_modify_original_request(self):
        req = httpx.Request("GET", "https://example.com", headers={"Authorization": "Bearer secret"})
        OtfRequestError("test", None, None, req)
        assert req.headers["authorization"] == "Bearer secret"

    def test_handles_none_request(self):
        err = OtfRequestError("test", None, None, None)
        assert err.request is None

    def test_handles_none_response(self):
        err = OtfRequestError("test", None, None, None)
        assert err.response is None


class TestValidateName:
    """Tests for name field validation in MemberApi."""

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            MemberApi._validate_name("", "first_name")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="must not be empty"):
            MemberApi._validate_name("   ", "first_name")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            MemberApi._validate_name("A" * 51, "first_name")

    def test_rejects_control_characters(self):
        with pytest.raises(ValueError, match="control characters"):
            MemberApi._validate_name("abc\x01def", "first_name")

    def test_rejects_html_brackets(self):
        with pytest.raises(ValueError, match="HTML-like"):
            MemberApi._validate_name("<script>alert(1)</script>", "first_name")

    def test_strips_whitespace(self):
        result = MemberApi._validate_name("  Jessica  ", "first_name")
        assert result == "Jessica"

    def test_allows_valid_name(self):
        result = MemberApi._validate_name("Jessica", "first_name")
        assert result == "Jessica"

    def test_allows_hyphenated_name(self):
        result = MemberApi._validate_name("Mary-Jane", "first_name")
        assert result == "Mary-Jane"

    def test_allows_accented_characters(self):
        result = MemberApi._validate_name("José", "first_name")
        assert result == "José"


class TestEnsureSecureDirectory:
    """Tests for cache directory permission hardening."""

    def test_creates_directory_with_0700(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            _ensure_secure_directory(path)
            mode = stat.S_IMODE(Path(path).stat().st_mode)
            assert mode == 0o700, f"Expected 0700, got {oct(mode)}"

    def test_tightens_existing_loose_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test_cache"
            os.makedirs(path, mode=0o755)
            _ensure_secure_directory(path)
            mode = stat.S_IMODE(Path(path).stat().st_mode)
            assert mode == 0o700, f"Expected 0700, got {oct(mode)}"
