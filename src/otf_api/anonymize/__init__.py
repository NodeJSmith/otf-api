"""Anonymization pipeline for OTF API fixtures.

Public API for the anonymization engine.
"""

from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer, ReplacementMap

__all__ = ["AnonymizeConfig", "Anonymizer", "ReplacementMap"]
