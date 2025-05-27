import os
import sys

sys.path.insert(0, os.path.abspath("../src"))  # type: ignore # noqa

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "OrangeTheory API"
copyright = "2025, Jessica Smith"
author = "Jessica Smith"
release = "0.13.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # for Google/NumPy-style docstrings
    "sphinxcontrib.autodoc_pydantic",  # renders BaseModel fields nicely
]


source_suffix = {
    ".rst": "restructuredtext",
}

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

myst_enable_extensions = ["fieldlist"]

PYDANTIC_IGNORE_FIELDS = [
    "dict",
    "copy",
    "parse_obj",
    "parse_raw",
    "parse_file",
    "schema",
    "schema_json",
    "model_validate",
    "model_validate_json",
    "model_validate_strings",
    "model_rebuild",
    "model_parametrized_name",
    "model_json_schema",
    "model_construct",
    "from_orm",
    "construct",
    "update_forward_refs",
    "validate",
    "json",
    "model_copy",
    "model_dump",
    "model_dump_json",
    "model_extra",
    "model_computed_fields",
    "model_fields",
    "model_fields_set",
    "model_config",
    "model_rebuild",
    "model_post_init",
]


autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "inherited-members": True,
    "exclude-members": ", ".join(PYDANTIC_IGNORE_FIELDS),
    "member-order": "groupwise",
}

typehints_fully_qualified = False  # makes types like `str` instead of `builtins.str`

# Optional: only show class signatures (not constructor separately)
autodoc_class_signature = "separated"  # or "mixed"
autodoc_inherit_docstrings = False

autodoc_default_flags = ["members"]
autosummary_generate = True
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_show_json = False
toc_object_entries_show_parents = "hide"  # Hide parent classes in the table of contents
master_doc = "index"
