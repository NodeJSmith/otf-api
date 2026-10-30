from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator

from otf_api.models.vocabulary import normalize_to


class StudioStatus(StrEnum):
    """Operational status of an OrangeTheory studio."""

    OTHER = "OTHER"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMING_SOON = "Coming Soon"
    TEMP_CLOSED = "Temporarily Closed"
    PERM_CLOSED = "Permanently Closed"
    UNKNOWN = "Unknown"


OpenStudioStatus = Annotated[StudioStatus | str, AfterValidator(normalize_to(StudioStatus))]
