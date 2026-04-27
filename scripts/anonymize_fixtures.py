#!/usr/bin/env python3
"""Batch anonymization script for OTF API fixture corpus.

Processes all JSON files in the input directory (default: fixtures/raw_responses),
writing anonymized output to the output directory (default: fixtures/anonymized).

Usage:
    uv run python scripts/anonymize_fixtures.py
    uv run python scripts/anonymize_fixtures.py --input-dir fixtures/raw_responses --output-dir fixtures/anonymized
    uv run python scripts/anonymize_fixtures.py --seed 12345
"""

import argparse
import logging
import sys
from pathlib import Path

from otf_api.anonymize import anonymize_batch
from otf_api.anonymize.anonymizer import AnonymizeConfig

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths (relative to repo root, not script location)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_INPUT_DIR = _REPO_ROOT / "fixtures" / "raw_responses"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "fixtures" / "anonymized"


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Anonymize OTF API fixture corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=_DEFAULT_INPUT_DIR,
        help=f"Directory containing raw fixture files (default: {_DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Directory to write anonymized output (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional integer seed for reproducible output (default: derived from first member UUID)",
    )
    parser.add_argument(
        "--strictness",
        choices=["permissive", "mask", "drop"],
        default="mask",
        help="How to handle unknown fields (default: mask)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return parser


def main() -> int:
    """Entry point — returns 0 on success, 1 on failure."""
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    seed: int | None = args.seed

    # Validate input directory exists
    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return 1

    logger.info("Starting batch anonymization")
    logger.info("  Input:  %s", input_dir)
    logger.info("  Output: %s", output_dir)
    if seed is not None:
        logger.info("  Seed:   %d (explicit)", seed)
    else:
        logger.info("  Seed:   auto-derived from first member UUID")

    config = AnonymizeConfig(strictness=args.strictness)
    if seed is not None:
        config = AnonymizeConfig(seed=seed, strictness=args.strictness)

    try:
        result = anonymize_batch(input_dir, output_dir, config=config)
    except OSError as exc:
        logger.error("Batch anonymization failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Summary output
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Anonymization Complete")
    print("=" * 60)
    print(f"  Files processed:          {result.files_processed}")
    print(f"  Files skipped (malformed):{result.files_skipped:>3}")
    print(f"  PII leaks found:          {len(result.validation.leaks)}")
    print(f"  Structural errors:        {len(result.validation.structural_errors)}")
    print(f"  Model parse errors:       {len(result.validation.model_parse_errors)}")
    print(f"  Replacement map written:  {result.replacement_map_path}")
    print()

    if result.validation.leaks:
        print(f"[FAIL] {len(result.validation.leaks)} PII leak(s) detected:")
        for leak in result.validation.leaks[:20]:
            print(f"  - {leak.file}:{leak.field_path} → {leak.real_value!r} ({leak.category})")
        if len(result.validation.leaks) > 20:
            print(f"  ... and {len(result.validation.leaks) - 20} more")
        print()

    if result.validation.structural_errors:
        print(f"[WARN] {len(result.validation.structural_errors)} structural error(s):")
        for err in result.validation.structural_errors[:10]:
            print(f"  - {err}")
        if len(result.validation.structural_errors) > 10:
            print(f"  ... and {len(result.validation.structural_errors) - 10} more")
        print()

    if result.validation.model_parse_errors:
        print(f"[WARN] {len(result.validation.model_parse_errors)} model parse error(s):")
        for err in result.validation.model_parse_errors[:10]:
            print(f"  - {err}")
        if len(result.validation.model_parse_errors) > 10:
            print(f"  ... and {len(result.validation.model_parse_errors) - 10} more")
        print()

    if result.validation.leaks:
        print("[FAIL] Anonymization complete but PII leaks were found. Review output before use.")
        return 1

    if result.files_skipped > 0:
        print(f"[WARN] {result.files_skipped} file(s) skipped due to malformed JSON.")

    print("[OK] Anonymization successful. Output is safe to review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
