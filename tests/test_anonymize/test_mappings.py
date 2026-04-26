"""Tests for PII field mappings."""


from otf_api.anonymize.mappings import FIELD_MAPPINGS, KNOWN_SAFE_FIELDS, FieldMapping

# All known PII field names from the fixture audit, organized per WP01 spec.
ALL_KNOWN_PII_FIELDS = {
    # Identity UUIDs
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
    "studioToken",
    "createdBy",
    "updatedBy",
    "studioAcsId",
    # Identity numeric
    "memberId",
    "mboUniqueId",
    "mbo_unique_id",
    "mbo_paying_unique_id",
    "studioId",
    "mboStudioId",
    "homeStudioId",
    "mboMemberId",
    "mboVisitId",
    "posPmtRefNo",
    "posSaleId",
    "mbo_staff_id",
    "mbo_booking_id",
    # Names
    "firstName",
    "lastName",
    "userName",
    "first_name",
    "last_name",
    "CoachName",
    # Email
    "email",
    "contactEmail",
    # Phone
    "phoneNumber",
    "homePhone",
    "workPhone",
    "phone_number",
    "phone",
    # Address
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
    # Birthday
    "birthDay",
    # Financial
    "ccLast4",
    "ccType",
    "price",
    # Biometric scalar
    "weight",
    "height",
    "maxHr",
    "automatedHr",
    "formulaMaxHr",
    "manualMaxHr",
    "age",
    "gender",
    # Biometric body comp
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
    "ecwOverTBWOfRightArm",
    "ecwOverTBWOfLeftArm",
    "ecwOverTBWOfTrunk",
    "ecwOverTBWOfRightLeg",
    "ecwOverTBWOfLeftLeg",
    "bfmControl",
    "pwt",
    "psmm",
    "pfatnew",
    # Biometric telemetry
    "hr",
    "startBpm",
    "endBpm",
    # Image URLs
    "imageUrl",
    "profilePictureUrl",
    "image_url",
    "coachImageUrl",
    "CoachImageUrl",
    # Timestamps
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
}


def _all_mapped_keys() -> set[str]:
    """Return the flat set of all JSON keys covered by all field mappings."""
    result: set[str] = set()
    for mapping in FIELD_MAPPINGS:
        for key in mapping.json_keys:
            result.add(key)
    return result


def test_field_mapping_is_dataclass() -> None:
    """FieldMapping is a dataclass with the expected attributes."""
    assert hasattr(FieldMapping, "__dataclass_fields__")
    fm = FIELD_MAPPINGS[0]
    assert hasattr(fm, "json_keys")
    assert hasattr(fm, "category")
    assert hasattr(fm, "strategy")
    assert hasattr(fm, "referential")


def test_all_pii_fields_have_mapping() -> None:
    """Every known PII field name must appear in at least one FieldMapping."""
    mapped_keys = _all_mapped_keys()
    missing = ALL_KNOWN_PII_FIELDS - mapped_keys
    assert not missing, f"PII fields with no mapping: {sorted(missing)}"


def test_no_mapping_overlap() -> None:
    """No field name should appear in two different FieldMapping entries."""
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for mapping in FIELD_MAPPINGS:
        for key in mapping.json_keys:
            if key in seen:
                duplicates.append(f"{key!r} appears in both {seen[key]!r} and {mapping.category!r}")
            else:
                seen[key] = mapping.category
    assert not duplicates, "Duplicate field keys across mappings:\n" + "\n".join(duplicates)


def test_known_safe_fields_not_mapped() -> None:
    """Fields in KNOWN_SAFE_FIELDS must not appear in any PII mapping."""
    mapped_keys = _all_mapped_keys()
    overlap = KNOWN_SAFE_FIELDS & mapped_keys
    assert not overlap, f"Safe fields that are also mapped as PII: {sorted(overlap)}"


def test_field_mappings_non_empty() -> None:
    """FIELD_MAPPINGS must contain at least one mapping."""
    assert len(FIELD_MAPPINGS) > 0


def test_known_safe_fields_non_empty() -> None:
    """KNOWN_SAFE_FIELDS must be a non-empty set."""
    assert isinstance(KNOWN_SAFE_FIELDS, (frozenset, set))
    assert len(KNOWN_SAFE_FIELDS) > 0
