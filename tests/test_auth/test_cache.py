"""Tests for src/otf_api/cache.py (OtfCache methods)."""

import pickle
import stat
import time
from pathlib import Path
from unittest.mock import patch

from otf_api.cache import OtfCache, clear_cache, get_cache, remove_legacy_diskcache


class Client:
    def __init__(self, member_uuid):
        self.member_uuid = member_uuid


def test_device_data_round_trip(tmp_cache):
    device_data = {
        "device_key": "dk-abc123",
        "device_group_key": "dgk-xyz789",
        "device_password": "dp-secret",
    }
    tmp_cache.write_device_data_to_cache(device_data)
    result = tmp_cache.read_device_data_from_cache()
    assert result == device_data


def test_device_data_all_empty_returns_empty_dict(tmp_cache):
    device_data = {
        "device_key": "",
        "device_group_key": "",
        "device_password": "",
    }
    tmp_cache.write_device_data_to_cache(device_data)
    result = tmp_cache.read_device_data_from_cache()
    assert result == {}


def test_token_data_round_trip(tmp_cache):
    token_data = {
        "access_token": "access-abc",
        "id_token": "id-xyz",
        "refresh_token": "refresh-123",
    }
    tmp_cache.write_token_data_to_cache(token_data)
    result = tmp_cache.read_token_data_from_cache()
    assert result == token_data


def test_token_data_expiry(tmp_cache):
    token_data = {
        "access_token": "access-abc",
        "id_token": "id-xyz",
        "refresh_token": "refresh-123",
    }
    tmp_cache.write_token_data_to_cache(token_data, expiration=1)
    time.sleep(2)
    result = tmp_cache.read_token_data_from_cache()
    assert result == {}


def test_token_data_all_empty_returns_empty_dict(tmp_cache):
    token_data = {
        "access_token": "",
        "id_token": "",
        "refresh_token": "",
    }
    tmp_cache.write_token_data_to_cache(token_data)
    result = tmp_cache.read_token_data_from_cache()
    assert result == {}


def test_clear_tokens_preserves_device_data(tmp_cache):
    device_data = {
        "device_key": "dk-abc",
        "device_group_key": "dgk-xyz",
        "device_password": "dp-secret",
    }
    token_data = {
        "access_token": "access-abc",
        "id_token": "id-xyz",
        "refresh_token": "refresh-123",
    }
    tmp_cache.write_device_data_to_cache(device_data)
    tmp_cache.write_token_data_to_cache(token_data)

    tmp_cache.clear_tokens()

    assert tmp_cache.read_token_data_from_cache() == {}
    assert tmp_cache.read_device_data_from_cache() == device_data


def test_clear_device_data_preserves_tokens(tmp_cache):
    device_data = {
        "device_key": "dk-abc",
        "device_group_key": "dgk-xyz",
        "device_password": "dp-secret",
    }
    token_data = {
        "access_token": "access-abc",
        "id_token": "id-xyz",
        "refresh_token": "refresh-123",
    }
    tmp_cache.write_device_data_to_cache(device_data)
    tmp_cache.write_token_data_to_cache(token_data)

    tmp_cache.clear_device_data()

    assert tmp_cache.read_device_data_from_cache() == {}
    assert tmp_cache.read_token_data_from_cache() == token_data


def test_clear_removes_everything(tmp_cache):
    device_data = {
        "device_key": "dk-abc",
        "device_group_key": "dgk-xyz",
        "device_password": "dp-secret",
    }
    token_data = {
        "access_token": "access-abc",
        "id_token": "id-xyz",
        "refresh_token": "refresh-123",
    }
    tmp_cache.write_device_data_to_cache(device_data)
    tmp_cache.write_token_data_to_cache(token_data)

    tmp_cache.clear()

    assert tmp_cache.read_device_data_from_cache() == {}
    assert tmp_cache.read_token_data_from_cache() == {}


def test_write_device_data_swallows_exception(tmp_cache):
    with patch("otf_api.cache.write_json", side_effect=RuntimeError("boom")):
        # Should not raise; exception is swallowed inside the method
        tmp_cache.write_device_data_to_cache({"device_key": "x", "device_group_key": "y", "device_password": "z"})


def test_read_device_data_swallows_exception(tmp_cache):
    with patch("otf_api.cache.read_json", side_effect=RuntimeError("boom")):
        result = tmp_cache.read_device_data_from_cache()
    assert result == {}


def test_write_token_data_swallows_exception(tmp_cache):
    with patch("otf_api.cache.write_json", side_effect=RuntimeError("boom")):
        tmp_cache.write_token_data_to_cache({"access_token": "a", "id_token": "b", "refresh_token": "c"})


def test_read_token_data_swallows_exception(tmp_cache):
    with patch("otf_api.cache.read_json", side_effect=RuntimeError("boom")):
        result = tmp_cache.read_token_data_from_cache()
    assert result == {}


def test_clear_tokens_swallows_exception(tmp_cache):
    with patch("otf_api.cache.Path.unlink", side_effect=RuntimeError("boom")):
        tmp_cache.clear_tokens()


def test_clear_device_data_swallows_exception(tmp_cache):
    with patch("otf_api.cache.Path.unlink", side_effect=RuntimeError("boom")):
        tmp_cache.clear_device_data()


def test_clear_swallows_exception(tmp_cache):
    with patch("otf_api.cache.Path.unlink", side_effect=RuntimeError("boom")):
        tmp_cache.clear()


def test_clear_cache_helper(tmp_path):
    """clear_cache() clears tokens, device data, and memoized responses from the module-level cache."""
    cache = OtfCache(str(tmp_path))
    device_data = {"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"}
    token_data = {"access_token": "at", "id_token": "it", "refresh_token": "rt"}
    cache.write_device_data_to_cache(device_data)
    cache.write_token_data_to_cache(token_data)
    cache.memoize(expire=600, tag="member_detail")(lambda self: {})(Client("m1"))

    with patch("otf_api.cache.get_cache", return_value=cache):
        clear_cache()

    assert cache.read_device_data_from_cache() == {}
    assert cache.read_token_data_from_cache() == {}
    assert not cache.responses_dir.exists()


def test_cache_files_are_owner_only_json(tmp_cache):
    tmp_cache.write_token_data_to_cache({"access_token": "a", "id_token": "b", "refresh_token": "c"}, expiration=60)
    tmp_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})

    for path in (tmp_cache.token_path, tmp_cache.device_path):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert '"access_token": "a"' in tmp_cache.token_path.read_text()


def test_unreadable_token_file_is_ignored(tmp_cache):
    """A pickle (or any non-JSON bytes) in the token file is treated as missing, never loaded."""
    tmp_cache.token_path.write_bytes(pickle.dumps({"access_token": "planted"}))

    assert tmp_cache.read_token_data_from_cache() == {}
    assert not tmp_cache.token_path.exists()


def test_device_data_writes_merge(tmp_cache):
    """Partial writes keep previously cached fields, as _set_tokens writes device data without the password."""
    tmp_cache.write_device_data_to_cache({"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"})
    tmp_cache.write_device_data_to_cache({"device_key": "dk2", "device_group_key": "dgk"})

    assert tmp_cache.read_device_data_from_cache() == {
        "device_key": "dk2",
        "device_group_key": "dgk",
        "device_password": "dp",
    }


def test_memoize_keys_by_member_and_arguments(tmp_cache):
    calls = []

    @tmp_cache.memoize(expire=600, tag="studio_detail")
    def get_studio_detail(self, studio_uuid):
        calls.append((self.member_uuid, studio_uuid))
        return {"member": self.member_uuid, "studio": studio_uuid}

    assert get_studio_detail(Client("m1"), "s1") == {"member": "m1", "studio": "s1"}
    assert get_studio_detail(Client("m1"), "s1") == {"member": "m1", "studio": "s1"}
    assert get_studio_detail(Client("m2"), "s1") == {"member": "m2", "studio": "s1"}
    assert get_studio_detail(Client("m1"), "s2") == {"member": "m1", "studio": "s2"}
    assert calls == [("m1", "s1"), ("m2", "s1"), ("m1", "s2")]


def test_memoize_expires(tmp_cache):
    calls = []

    @tmp_cache.memoize(expire=1, tag="telemetry")
    def get_telemetry(self):
        calls.append(1)
        return {"n": len(calls)}

    assert get_telemetry(Client("m1")) == {"n": 1}
    time.sleep(1.1)
    assert get_telemetry(Client("m1")) == {"n": 2}


def test_evict_removes_only_that_tag(tmp_cache):
    calls = []

    @tmp_cache.memoize(expire=600, tag="member_detail")
    def get_member_detail(self):
        calls.append("member")
        return {}

    @tmp_cache.memoize(expire=600, tag="studio_detail")
    def get_studio_detail(self):
        calls.append("studio")
        return {}

    client = Client("m1")
    get_member_detail(client)
    get_studio_detail(client)
    tmp_cache.evict("member_detail")
    get_member_detail(client)
    get_studio_detail(client)

    assert calls == ["member", "studio", "member"]


def test_memoize_survives_cache_write_failure(tmp_cache):
    @tmp_cache.memoize(expire=600, tag="member_detail")
    def get_member_detail(self):
        return {"ok": True}

    with patch("otf_api.cache.write_json", side_effect=OSError("disk full")):
        assert get_member_detail(Client("m1")) == {"ok": True}


def test_clear_removes_memoized_responses(tmp_cache):
    @tmp_cache.memoize(expire=600, tag="member_detail")
    def get_member_detail(self):
        return {}

    get_member_detail(Client("m1"))
    tmp_cache.clear()

    assert not tmp_cache.responses_dir.exists()


def test_remove_legacy_diskcache(tmp_path):
    for name in ("cache.db", "cache.db-wal", "cache.db-shm"):
        (tmp_path / name).write_bytes(b"old")
    (tmp_path / "3f" / "a1").mkdir(parents=True)
    (tmp_path / "3f" / "a1" / "x.val").write_bytes(b"old")
    (tmp_path / "tokens.json").write_text("{}")
    (tmp_path / "responses").mkdir()

    remove_legacy_diskcache(str(tmp_path))

    assert sorted(p.name for p in tmp_path.iterdir()) == ["responses", "tokens.json"]


def test_get_cache_removes_legacy_diskcache(tmp_path):
    (tmp_path / "cache.db").write_bytes(b"old")

    with patch("otf_api.cache._CACHE", None), patch("otf_api.cache.get_cache_dir", return_value=str(tmp_path)):
        cache = get_cache()

    assert cache.directory == Path(tmp_path)
    assert not (tmp_path / "cache.db").exists()


def test_purge_expired_responses(tmp_cache):
    @tmp_cache.memoize(expire=600, tag="member_detail")
    def get_member_detail(self):
        return {}

    @tmp_cache.memoize(expire=600, tag="telemetry")
    def get_telemetry(self, summary_id):
        return {}

    get_member_detail(Client("m1"))
    get_telemetry(Client("m1"), "old")

    with patch("otf_api.cache.time.time", return_value=time.time() + 601):
        get_member_detail(Client("m1"))  # refreshed, so it outlives the purge below
        tmp_cache.purge_expired_responses()

    assert [p.parent.name for p in tmp_cache.responses_dir.glob("*/*.json")] == ["member_detail"]
