"""Anonymization pipeline for OTF API fixtures.

Public API for the anonymization engine.
"""

from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer, ReplacementMap
from otf_api.anonymize.validator import LeakReport, PiiValidator, ValidationResult, collect_real_values


def validate_anonymized(
    original: dict,
    anonymized: dict,
    filename: str,
    known_real_values: set[str] | None = None,
) -> ValidationResult:
    """Convenience wrapper around PiiValidator.validate_file.

    Args:
        original: The original (pre-anonymization) fixture dict.
        anonymized: The anonymized fixture dict to validate.
        filename: The fixture filename (used for leak scanning and model lookup).
        known_real_values: Set of real PII value strings to scan for. If None,
            an empty set is used (structural and model checks only).

    Returns:
        A ValidationResult summarising all findings.
    """
    validator = PiiValidator(known_real_values=known_real_values or set())
    return validator.validate_file(original, anonymized, filename)


__all__ = [
    "AnonymizeConfig",
    "Anonymizer",
    "LeakReport",
    "PiiValidator",
    "ReplacementMap",
    "ValidationResult",
    "collect_real_values",
    "validate_anonymized",
]
