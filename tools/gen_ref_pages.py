"""Generate per-module reference stubs for mkdocstrings."""

import os
import shutil
from pathlib import Path

import mkdocs_gen_files

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
VIRTUAL_REF_ROOT = Path("reference")
DEBUG = bool(os.environ.get("GEN_REF_DEBUG"))

# Public API allowlist — only modules in this set will have reference stubs generated.
PUBLIC_MODULES: frozenset[str] = frozenset(
    {
        # --- API layer ---
        "otf_api.api.api",
        "otf_api.api.bookings.booking_api",
        "otf_api.api.members.member_api",
        "otf_api.api.studios.studio_api",
        "otf_api.api.workouts.workout_api",
        # --- Auth ---
        "otf_api.auth.user",
        # --- Models: Bookings ---
        "otf_api.models.bookings.bookings",
        "otf_api.models.bookings.bookings_v2",
        "otf_api.models.bookings.classes",
        "otf_api.models.bookings.enums",
        "otf_api.models.bookings.filters",
        # --- Models: Members ---
        "otf_api.models.members.member_detail",
        "otf_api.models.members.member_membership",
        "otf_api.models.members.member_purchases",
        "otf_api.models.members.notifications",
        # --- Models: Studios ---
        "otf_api.models.studios.studio_detail",
        "otf_api.models.studios.studio_services",
        "otf_api.models.studios.enums",
        # --- Models: Workouts ---
        "otf_api.models.workouts.workout",
        "otf_api.models.workouts.performance_summary",
        "otf_api.models.workouts.telemetry",
        "otf_api.models.workouts.body_composition_list",
        "otf_api.models.workouts.challenge_tracker_content",
        "otf_api.models.workouts.challenge_tracker_detail",
        "otf_api.models.workouts.lifetime_stats",
        "otf_api.models.workouts.out_of_studio_workout_history",
        "otf_api.models.workouts.enums",
        # --- Base / Utilities ---
        "otf_api.exceptions",
        "otf_api.models.base",
        "otf_api.models.mixins",
    }
)


def format_title(part: str) -> str:
    """Convert a snake_case module name part to a Title Case display name."""
    return " ".join(word.capitalize() for word in part.split("_"))


def main() -> None:
    """Generate API reference pages for all public modules."""
    nav = mkdocs_gen_files.Nav()

    ref_disk_dir = ROOT / "docs" / VIRTUAL_REF_ROOT
    if ref_disk_dir.exists():
        shutil.rmtree(ref_disk_dir)

    if DEBUG:
        print("[gen-ref] generating API reference stubs...", flush=True)

    # Write the reference overview page.
    index_content = (
        "# API Reference\n\n"
        "The API reference is auto-generated from source docstrings."
        " It covers all public modules in otf-api.\n\n"
        "Browse the modules in the navigation sidebar, or jump directly to a section:\n\n"
        "- **API** — `otf_api.api.api` · `otf_api.api.bookings` · `otf_api.api.members`"
        " · `otf_api.api.studios` · `otf_api.api.workouts`\n"
        "- **Auth** — `otf_api.auth.user`\n"
        "- **Models** — `otf_api.models.bookings` · `otf_api.models.members`"
        " · `otf_api.models.studios` · `otf_api.models.workouts`\n"
        "- **Base** — `otf_api.models.base` · `otf_api.models.mixins`"
        " · `otf_api.exceptions`\n"
    )
    with mkdocs_gen_files.open(VIRTUAL_REF_ROOT / "index.md", "w") as index_file:
        index_file.write(index_content)
    nav[["Overview"]] = "index.md"

    for path in sorted(SRC_DIR.rglob("*.py")):
        module_parts = path.relative_to(SRC_DIR).with_suffix("").parts

        if not module_parts:
            continue

        if module_parts[-1] in {"__main__", "__version__"}:
            continue

        doc_path = Path(*module_parts).with_suffix(".md")
        full_doc_path = VIRTUAL_REF_ROOT / doc_path
        parts = module_parts

        if parts[-1] == "__init__":
            parts = parts[:-1]
            if not parts:
                continue
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")

        module_path = ".".join(parts)

        if module_path not in PUBLIC_MODULES:
            if DEBUG:
                print(f"[gen-ref] skipping {module_path} (not in allowlist)")
            continue

        nav_entry = [format_title(part) for part in parts]
        nav[nav_entry] = doc_path.as_posix()

        if DEBUG:
            print(f"[gen-ref] writing {full_doc_path} for {module_path}")

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            fd.write(f"::: {module_path}\n")

        mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(ROOT))

    summary_path = VIRTUAL_REF_ROOT / "SUMMARY.md"
    with mkdocs_gen_files.open(summary_path, "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


if __name__ in {"__main__", "<run_path>"}:
    main()
