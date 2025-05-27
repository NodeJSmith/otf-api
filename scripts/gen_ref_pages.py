import shutil
from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = Path(__file__).parent.parent
src = root / "src"

skip_names = ["client", "compat", "utils", "exceptions", "auth", "cache", "base", "mixins"]

REF_DIR = root / "docs" / "reference"
if REF_DIR.exists():
    shutil.rmtree(REF_DIR)

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] in ["__main__", "__version__"]:
        continue

    if any(skip_name in path.stem for skip_name in skip_names):
        continue

    if path.name == "api.py":
        title_parts = ["Otf API", "Otf"]
    else:
        title_parts = []
        for part in parts:
            sub_parts = part.split("_")
            for i, sub_part in enumerate(sub_parts):
                if sub_part in ["api", "hr"]:
                    sub_parts[i] = sub_part.upper()
                else:
                    sub_parts[i] = sub_part.capitalize()
            part = " ".join(sub_parts)
            title_parts.append(part)
    print(title_parts)

    nav[title_parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
