from pydantic import Field

from otf_api.models.base import OtfItemBase


class SmsNotificationSettings(OtfItemBase):
    """SMS and phone call notification preferences for a member."""

    is_promotional_sms_opt_in: bool | None = Field(
        None, validation_alias="isPromotionalSmsOptIn", description="Opted in to promotional SMS messages."
    )
    is_transactional_sms_opt_in: bool | None = Field(
        None, validation_alias="isTransactionalSmsOptIn", description="Opted in to transactional SMS messages."
    )
    is_promotional_phone_opt_in: bool | None = Field(
        None, validation_alias="isPromotionalPhoneOptIn", description="Opted in to promotional phone calls."
    )
    is_transactional_phone_opt_in: bool | None = Field(
        None, validation_alias="isTransactionalPhoneOptIn", description="Opted in to transactional phone calls."
    )


class EmailNotificationSettings(OtfItemBase):
    """Email notification preferences for a member."""

    is_system_email_opt_in: bool | None = Field(
        None, validation_alias="isSystemEmailOptIn", description="Opted in to system emails."
    )
    is_promotional_email_opt_in: bool | None = Field(
        None, validation_alias="isPromotionalEmailOptIn", description="Opted in to promotional emails."
    )
    is_transactional_email_opt_in: bool | None = Field(
        None, validation_alias="isTransactionalEmailOptIn", description="Opted in to transactional emails."
    )
    email: str | None = Field(None, description="Email address for notifications.")
