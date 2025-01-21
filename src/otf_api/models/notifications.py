from pydantic import Field

from otf_api.models.base import OtfItemBase


class SmsNotificationSettings(OtfItemBase):
    is_promotional_sms_opt_in: bool | None = Field(None, alias="isPromotionalSmsOptIn")
    is_transactional_sms_opt_in: bool | None = Field(None, alias="isTransactionalSmsOptIn")
    is_promotional_phone_opt_in: bool | None = Field(None, alias="isPromotionalPhoneOptIn")
    is_transactional_phone_opt_in: bool | None = Field(None, alias="isTransactionalPhoneOptIn")


class EmailNotificationSettings(OtfItemBase):
    is_system_email_opt_in: bool | None = Field(None, alias="isSystemEmailOptIn")
    is_promotional_email_opt_in: bool | None = Field(None, alias="isPromotionalEmailOptIn")
    is_transactional_email_opt_in: bool | None = Field(None, alias="isTransactionalEmailOptIn")
    email: str | None = None
