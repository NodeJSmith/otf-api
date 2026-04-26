"""PII field classifications for the OTF API anonymization pipeline.

Each FieldMapping covers one logical PII category and lists all known JSON key
aliases that belong to it.  The ``strategy`` callable is used by the Anonymizer
(implemented in WP02) to produce a replacement value.  ``referential=True``
means the same real value must always map to the same fake value within a
batch.
"""

import dataclasses
from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class FieldMapping:
    """Describes how a set of JSON keys should be anonymized.

    Attributes:
        json_keys: All known alias forms of this field name across fixtures.
        category: Human-readable category label (e.g. "identity_uuid").
        strategy: Callable that accepts ``(generators, original_value)`` and
            returns the replacement value.  Populated at module level once
            ``generators`` is importable; the Anonymizer resolves it at runtime.
        referential: When True the Anonymizer must return the same fake value
            every time it encounters the same real value.
    """

    json_keys: tuple[str, ...]
    category: str
    strategy: Callable[..., object]
    referential: bool


# ---------------------------------------------------------------------------
# Sentinel strategy callables — lightweight placeholders used by the mapping
# definitions.  The real Anonymizer wires these to generator methods at call
# time (WP02).  They are *not* called directly during mapping definition.
# ---------------------------------------------------------------------------


def _strategy_uuid(*_: object) -> str:
    return ""


def _strategy_numeric_id(*_: object) -> int:
    return 0


def _strategy_name(*_: object) -> str:
    return ""


def _strategy_email(*_: object) -> str:
    return ""


def _strategy_phone(*_: object) -> str:
    return ""


def _strategy_address(*_: object) -> dict[str, str]:
    return {}


def _strategy_birthday(*_: object) -> str:
    return ""


def _strategy_cc_last4(*_: object) -> str:
    return ""


def _strategy_cc_type(*_: object) -> str:
    return ""


def _strategy_price(*_: object) -> float:
    return 0.0


def _strategy_gender(*_: object) -> str:
    return ""


def _strategy_biometric_scalar(*_: object) -> float:
    return 0.0


def _strategy_body_comp(*_: object) -> float:
    return 0.0


def _strategy_telemetry_hr(*_: object) -> int:
    return 0


def _strategy_redacted(*_: object) -> str:
    return "REDACTED"


def _strategy_image_url(*_: object) -> str:
    return ""


def _strategy_timestamp(*_: object) -> str:
    return ""


# ---------------------------------------------------------------------------
# Field mappings — one entry per logical PII category.
# ---------------------------------------------------------------------------

FIELD_MAPPINGS: list[FieldMapping] = [
    # ------------------------------------------------------------------
    # Identity — UUIDs
    # Note: studioToken appears here because it doubles as a UUID-format
    # identifier in some responses AND as a bearer token (REDACTED strategy
    # covers it in the Auth token mapping below).  To avoid overlap the UUID
    # mapping omits studioToken and it lives only in the Auth token category.
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "memberUUId",
            "cognitoId",
            "person_id",
            "mboId",
            "otfAcsId",
            "studioUUId",
            "coachUUId",
            "classBookingUUId",
            "memberAddressUUId",
            "memberMembershipUUId",
            "memberPurchaseUUId",
            "memberProfileUUId",
            "scanResultUUId",
            "workoutUUId",
            "class_uuid",
            "class_id",
            "booking_id",
            "booking_uuid",
            "studio_uuid",
            "paying_studio_id",
            "createdBy",
            "updatedBy",
            "studioAcsId",
            # v1 API camelCase UUID fields
            "classUUId",
            # yuzu API (api.yuzu.orangetheory.com) UUID fields
            "memberUuid",
            "classHistoryUuid",
            # v2 API (api.orangetheory.io) snake_case variants
            "member_id",
            "ot_base_class_uuid",
        ),
        category="identity_uuid",
        strategy=_strategy_uuid,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Identity — numeric IDs
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "memberId",
            "mboUniqueId",
            "mbo_unique_id",
            "mbo_paying_unique_id",
            "studioId",
            "mboStudioId",
            "mbo_studio_id",
            "homeStudioId",
            "mboMemberId",
            "mboVisitId",
            "posPmtRefNo",
            "posSaleId",
            "mbo_staff_id",
            "mbo_booking_id",
        ),
        category="identity_numeric",
        strategy=_strategy_numeric_id,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Names
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "firstName",
            "lastName",
            "userName",
            "first_name",
            "last_name",
            "CoachName",
        ),
        category="name",
        strategy=_strategy_name,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "email",
            "contactEmail",
            # body-composition endpoint (api.orangetheory.co) stores the member's
            # email address in a top-level "id" field — unusual but confirmed in
            # fixtures.  Short sequential IDs that also use "id" (e.g. social media
            # link IDs like "5", "6") are excluded from filename substitution via
            # the _MIN_SUBSTITUTE_LEN guard in _substitute_from_map.
            "id",
        ),
        category="email",
        strategy=_strategy_email,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Phone
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "phoneNumber",
            "homePhone",
            "workPhone",
            "phone_number",
            "phone",
        ),
        category="phone",
        strategy=_strategy_phone,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Address
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "address1",
            "addressLine1",
            "address2",
            "addressLine2",
            "physicalAddress",
            "billToAddress",
            "shipToAddress",
            "city",
            "physicalCity",
            "suburb",
            "billToCity",
            "state",
            "physicalState",
            "territory",
            "postalCode",
            "physicalPostalCode",
            "country",
            "physicalCountry",
            # v2 API (api.orangetheory.io) snake_case variants
            "line1",
            "line2",
            "postal_code",
        ),
        category="address",
        strategy=_strategy_address,
        referential=True,
    ),
    # ------------------------------------------------------------------
    # Birthday
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=("birthDay",),
        category="birthday",
        strategy=_strategy_birthday,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Financial — split by type: 4-digit string, card brand, decimal amount
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=("ccLast4",),
        category="financial_cc_last4",
        strategy=_strategy_cc_last4,
        referential=False,
    ),
    FieldMapping(
        json_keys=("ccType",),
        category="financial_cc_type",
        strategy=_strategy_cc_type,
        referential=False,
    ),
    FieldMapping(
        json_keys=(
            "price",
            "onlinePrice",
        ),
        category="financial_price",
        strategy=_strategy_price,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Gender — enum string, not a numeric scalar
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=("gender",),
        category="gender",
        strategy=_strategy_gender,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Biometric — scalar values
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "weight",
            "height",
            "maxHr",
            "automatedHr",
            "formulaMaxHr",
            "manualMaxHr",
            "age",
        ),
        category="biometric_scalar",
        strategy=_strategy_biometric_scalar,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Biometric — body composition (InBody scan fields)
    # Field names are the validation_alias values from body_composition_list.py
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "tbw",
            "dlm",
            "bfm",
            "lbm",
            "smm",
            "bmi",
            "pbf",
            "bmr",
            "lbmOfRightArm",
            "lbmOfLeftArm",
            "lbmOfTrunk",
            "lbmOfRightLeg",
            "lbmOfLeftLeg",
            "lbmPercentOfRightArm",
            "lbmPercentOfLeftArm",
            "lbmPercentOfTrunk",
            "lbmPercentOfRightLeg",
            "lbmPercentOfLeftLeg",
            "bfmOfRightArm",
            "bfmOfLeftArm",
            "bfmOfTrunk",
            "bfmOfRightLeg",
            "bfmOfLeftLeg",
            "tbwOfRightArm",
            "tbwOfLeftArm",
            "tbwOfTrunk",
            "tbwOfRightLeg",
            "tbwOfLeftLeg",
            "icwOfRightArm",
            "icwOfLeftArm",
            "icwOfTrunk",
            "icwOfRightLeg",
            "icwOfLeftLeg",
            "ecwOfRightArm",
            "ecwOfLeftArm",
            "ecwOfTrunk",
            "ecwOfRightLeg",
            "ecwOfLeftLeg",
            # Actual validation_alias from ExtraCellularWaterOverTotalBodyWater uses uppercase TBW
            "ecwOverTBWOfRightArm",
            "ecwOverTBWOfLeftArm",
            "ecwOverTBWOfTrunk",
            "ecwOverTBWOfRightLeg",
            "ecwOverTBWOfLeftLeg",
            "bfmControl",
            "pwt",
            "psmm",
            "pfatnew",
        ),
        category="biometric_body_comp",
        strategy=_strategy_body_comp,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Biometric — telemetry (HR arrays and zone boundaries)
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=("hr", "startBpm", "endBpm"),
        category="biometric_telemetry",
        strategy=_strategy_telemetry_hr,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Auth tokens — always redacted
    # studioToken lives here (not in identity_uuid) because the primary
    # concern is that it never leaks as a bearer credential.
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=("studioToken",),
        category="auth_token",
        strategy=_strategy_redacted,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Image URLs
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "imageUrl",
            "profilePictureUrl",
            "image_url",
            "coachImageUrl",
            "CoachImageUrl",
        ),
        category="image_url",
        strategy=_strategy_image_url,
        referential=False,
    ),
    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    FieldMapping(
        json_keys=(
            "bookedDate",
            "checkedInDate",
            "cancelledDate",
            "createdDate",
            "updatedDate",
            "workoutDate",
            "startTime",
            "endTime",
            "testDatetime",
            "classStartTime",
            "classTime",
            "firstVisitDate",
            "lastClassVisitedDate",
            "lastClassBookedDate",
            "paymentDate",
            "memberPurchaseDateTime",
            "assignedAt",
        ),
        category="timestamp",
        strategy=_strategy_timestamp,
        referential=False,
    ),
]

# ---------------------------------------------------------------------------
# Known-safe fields — these must never be anonymized.  They carry no PII;
# they are class type names, equipment labels, challenge categories, timezone
# strings, and similar non-personal metadata.
# ---------------------------------------------------------------------------

KNOWN_SAFE_FIELDS: frozenset[str] = frozenset(
    {
        # Class / workout type labels
        "classType",
        "classTypeName",
        "className",
        "classDescription",
        "workoutType",
        "name",
        "description",
        # Challenge and category metadata
        "challengeCategory",
        "challengeSubCategory",
        "challengeName",
        "challengeType",
        "equipmentName",
        "equipment",
        # Status / enum values
        "status",
        "bookingStatus",
        "memberStatus",
        "subscriptionType",
        "membershipType",
        "classBookingType",
        # Timezone and locale
        "timezone",
        "timeZone",
        "locale",
        "currency",
        "currencyAlpha",
        # Studio descriptive metadata
        "studioName",
        "studioStatus",
        "studioType",
        "phoneNumberFormat",
        "studioPhysicalRegionName",
        "studioPhysicalRegionId",
        "regionId",
        # Telemetry metadata (non-HR)
        "version",
        "orange_time",
        "red_time",
        "green_time",
        "black_time",
        "blue_time",
        "total_calories",
        "total_steps",
        "total_splat_points",
        "active_time",
        # Coach metadata (non-PII)
        "coachType",
        # InBody scan metadata (non-biometric labels)
        "inBodyType",
        "inBodyScore",
        # Distance / unit fields
        "unit",
        "distanceUnit",
        # Boolean flags
        "isHomeStudio",
        "isActive",
        "isOpen",
        "isVisible",
        "isHidden",
        "isFeatured",
        "isPremium",
        "isVirtual",
        "isLive",
        # Pagination / API metadata
        "pageIndex",
        "pageSize",
        "totalCount",
        "pageCount",
    }
)
