from enum import StrEnum


class StudioStatus(StrEnum):
    """Operational status of an OrangeTheory studio."""

    OTHER = "OTHER"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMING_SOON = "Coming Soon"
    TEMP_CLOSED = "Temporarily Closed"
    PERM_CLOSED = "Permanently Closed"
    UNKNOWN = "Unknown"
