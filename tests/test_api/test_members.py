"""Tests for MemberApi read-only methods."""

from otf_api.models.members.member_detail import MemberDetail
from otf_api.models.members.member_membership import MemberMembership
from otf_api.models.members.member_purchases import MemberPurchase
from otf_api.models.members.notifications import EmailNotificationSettings, SmsNotificationSettings
from otf_api.models.studios.studio_detail import StudioDetail


def test_get_member_detail(mock_otf) -> None:
    result = mock_otf.members.get_member_detail()

    assert isinstance(result, MemberDetail)
    assert isinstance(result.member_uuid, str)
    assert result.member_uuid != ""
    assert isinstance(result.email, str)
    assert result.home_studio is not None
    assert isinstance(result.home_studio.studio_uuid, str)


def test_get_member_membership(mock_otf) -> None:
    result = mock_otf.members.get_member_membership()

    assert isinstance(result, MemberMembership)
    assert result.current is not None
    assert isinstance(result.current, bool)


def test_get_member_purchases(mock_otf) -> None:
    result = mock_otf.members.get_member_purchases()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(p, MemberPurchase) for p in result)

    first = result[0]
    assert isinstance(first.purchase_uuid, str)
    assert isinstance(first.studio, StudioDetail)
    assert isinstance(first.studio.studio_uuid, str)


def test_get_sms_notification_settings(mock_otf) -> None:
    result = mock_otf.members.get_sms_notification_settings()

    assert isinstance(result, SmsNotificationSettings)
    assert isinstance(result.is_promotional_sms_opt_in, bool)
    assert isinstance(result.is_transactional_sms_opt_in, bool)


def test_get_email_notification_settings(mock_otf) -> None:
    result = mock_otf.members.get_email_notification_settings()

    assert isinstance(result, EmailNotificationSettings)
    assert isinstance(result.email, str)
    assert isinstance(result.is_promotional_email_opt_in, bool)
