from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase


class LatestAgreement(OtfItemBase):
    file_url: str = Field(..., alias="fileUrl")
    agreement_id: int = Field(..., alias="agreementId")
    agreement_uuid: str = Field(..., alias="agreementUUId")
    agreement_datetime: datetime = Field(..., alias="agreementDatetime")
    agreement_type_id: int = Field(..., alias="agreementTypeId")
    platform: None
    locale: str
    version: str
    created_by: str = Field(..., alias="createdBy")
    created_date: datetime = Field(..., alias="createdDate")
    updated_by: str = Field(..., alias="updatedBy")
    updated_date: datetime = Field(..., alias="updatedDate")
    is_deleted: bool = Field(..., alias="isDeleted")
