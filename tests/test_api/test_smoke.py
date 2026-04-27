"""Smoke tests: verifies the mock client pipeline end-to-end."""

from otf_api.models.members.member_detail import MemberDetail


def test_get_member_detail(mock_otf):
    """Verify fixture loading -> route matching -> HTTP interception -> Pydantic parsing."""
    result = mock_otf.members.get_member_detail()

    assert isinstance(result, MemberDetail)
    assert isinstance(result.member_uuid, str)
    assert result.member_uuid != ""
