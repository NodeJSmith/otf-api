"""Tests for src/otf_api/cache.py (OtfCache methods)."""

import time
from unittest.mock import patch

from diskcache_community import Cache, Disk, SafeDisk

from otf_api.auth.auth import OtfCognito
from otf_api.cache import OtfCache, clear_cache, get_cache, memoize_by_member


class Planted:
    def __reduce__(self):
        return (OtfCognito, ("planted-user", "planted-password"))


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
    with patch.object(tmp_cache, "set", side_effect=RuntimeError("boom")):
        # Should not raise; exception is swallowed inside the method
        tmp_cache.write_device_data_to_cache({"device_key": "x", "device_group_key": "y", "device_password": "z"})


def test_read_device_data_swallows_exception(tmp_cache):
    with patch.object(tmp_cache, "get", side_effect=RuntimeError("boom")):
        result = tmp_cache.read_device_data_from_cache()
    assert result == {}


def test_write_token_data_swallows_exception(tmp_cache):
    with patch.object(tmp_cache, "set", side_effect=RuntimeError("boom")):
        tmp_cache.write_token_data_to_cache({"access_token": "a", "id_token": "b", "refresh_token": "c"})


def test_read_token_data_swallows_exception(tmp_cache):
    with patch.object(tmp_cache, "get", side_effect=RuntimeError("boom")):
        result = tmp_cache.read_token_data_from_cache()
    assert result == {}


def test_clear_tokens_swallows_exception(tmp_cache):
    with patch.object(tmp_cache, "evict", side_effect=RuntimeError("boom")):
        tmp_cache.clear_tokens()


def test_clear_device_data_swallows_exception(tmp_cache):
    with patch.object(tmp_cache, "evict", side_effect=RuntimeError("boom")):
        tmp_cache.clear_device_data()


def test_clear_swallows_exception(tmp_cache):
    with patch("otf_api.cache.Cache.clear", side_effect=RuntimeError("boom")):
        tmp_cache.clear()


def test_clear_cache_helper(tmp_path):
    """clear_cache() clears tokens and device data from the module-level cache."""
    cache = OtfCache(str(tmp_path))
    device_data = {"device_key": "dk", "device_group_key": "dgk", "device_password": "dp"}
    token_data = {"access_token": "at", "id_token": "it", "refresh_token": "rt"}
    cache.write_device_data_to_cache(device_data)
    cache.write_token_data_to_cache(token_data)

    with patch("otf_api.cache.get_cache", return_value=cache):
        clear_cache()

    assert cache.read_device_data_from_cache() == {}
    assert cache.read_token_data_from_cache() == {}


def test_get_cache_ignores_planted_pickle(tmp_path):
    with Cache(str(tmp_path), disk=Disk) as other_writer:
        other_writer.set("id_token", Planted(), tag="token")

    with (
        patch("otf_api.cache._CACHE", None),
        patch("otf_api.cache.get_cache_dir", return_value=str(tmp_path)),
        patch.object(OtfCognito, "handle_login") as handle_login,
    ):
        cache = get_cache()
        tokens = cache.read_token_data_from_cache()
    cache.close()

    assert tokens == {}
    handle_login.assert_not_called()


def test_memoize_by_member_keys_by_member_uuid(tmp_path):
    class Client:
        def __init__(self, member_uuid):
            self.member_uuid = member_uuid

    requests = []
    cache = OtfCache(str(tmp_path), disk=SafeDisk.with_options(on_error="miss"))
    with patch("otf_api.cache._CACHE", cache):

        @memoize_by_member(expire=600, tag="studio_detail")
        def get_studio_detail(self, studio_uuid):
            requests.append((self.member_uuid, studio_uuid))
            return {"member": self.member_uuid, "studio": studio_uuid}

    first, second = Client("member-1"), Client("member-2")
    assert get_studio_detail(first, "studio-1") == {"member": "member-1", "studio": "studio-1"}
    assert get_studio_detail(Client("member-1"), "studio-1") == {"member": "member-1", "studio": "studio-1"}
    assert get_studio_detail(second, "studio-1") == {"member": "member-2", "studio": "studio-1"}
    assert requests == [("member-1", "studio-1"), ("member-2", "studio-1")]
    cache.close()
