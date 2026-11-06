# SPHINX CONFIGURATION FILE
# #######################################################################
# This is a simple template for the modern configuration file for sphinx
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# TEMPLATE INSTRUCTIONS
# ***********************************************************************
# 1) look for '[CHANGE THIS]' for mandatory modifications
# 2) look for '[CHECK THIS]' for possible modifications
# 3) look for '[EXAMPLE]' for simple examples (comment or uncomment it if needed)
# 4) look for '[ADD MORE IF NEDDED]' for possible extra features
# 5) placeholders are designated by curly braces: {replace-this}


# REPO LAYOUT
# ***********************************************************************
import os
import sys

"""  
for src layout (default)
myrepo/  
├── src/  
│   └── myrepo/  
│        ├── __init__.py  
│        └── module.py  
└── docs/   
use >> sys.path.insert(0, os.path.abspath("../src")) 
"""
sys.path.insert(0, os.path.abspath("../src"))  # src layout


# CATALOG PAGES
# ***********************************************************************
# the variables, statistics and flags pages include tables built here from
# the shipped catalogs, so every build matches the package data
import csv
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
CATALOGS_DIR = DOCS_DIR.parent / "src" / "plans" / "data" / "catalogs"
CATALOG_PAGES_DIR = DOCS_DIR / "generated" / "catalogs"


def read_catalog(name):
    """
    Read a shipped catalog file.

    :param name: catalog file stem, eg ``"variables"``
    :type name: str
    :return: rows as dicts, in file order
    :rtype: list[dict]
    """
    with open(CATALOGS_DIR / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def rst_text(value):
    # plain text with RST inline markup characters escaped
    for char in ("\\", "*", "`", "|", "_"):
        value = value.replace(char, "\\" + char)
    return value


def rst_literal(value):
    return f"``{value}``" if value else ""


def rst_math(value):
    return f":math:`{value}`" if value else ""


def list_table(rows, columns):
    """
    Render catalog rows as an RST list-table.

    :param rows: catalog rows
    :type rows: list[dict]
    :param columns: ``{header: function(row) -> cell}``, in display order
    :type columns: dict
    :return: RST lines
    :rtype: list[str]
    """
    lines = [".. list-table::", "   :header-rows: 1", "   :widths: auto", ""]
    table = [list(columns)] + [[cell(row) for cell in columns.values()] for row in rows]
    for cells in table:
        for j, cell in enumerate(cells):
            lines.append((f"   * - {cell}" if j == 0 else f"     - {cell}").rstrip())
    return lines + [""]


def build_catalog_pages():
    """
    Write the table includes of the variables, statistics and flags pages.

    :return: None
    :rtype: None
    """
    CATALOG_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # variables: one table per discipline
    variables = read_catalog(name="variables")
    columns = {
        "Code": lambda r: rst_literal(r["code"]),
        "Name": lambda r: rst_text(r["name"]),
        "Alias": lambda r: rst_literal(r["alias"]),
        "Symbol": lambda r: rst_math(r["symbol"]),
        "Units": lambda r: rst_literal(r["units"]),
        "Type": lambda r: rst_literal(r["dtype"]),
        "Domain": lambda r: rst_literal(r["domain"]),
        "Theme": lambda r: rst_text(r["theme"]),
        "Category": lambda r: rst_text(r["category"]),
    }
    lines = []
    for discipline in sorted({r["discipline"] for r in variables}):
        rows = [r for r in variables if r["discipline"] == discipline]
        lines += [discipline, "=" * len(discipline), ""]
        lines += list_table(rows=rows, columns=columns)
    (CATALOG_PAGES_DIR / "variables.rst").write_text("\n".join(lines), encoding="utf-8")

    # statistics: a single table
    columns = {
        "Name": lambda r: rst_literal(r["name"]),
        "Alias": lambda r: rst_literal(r["alias"]),
        "Title": lambda r: rst_text(r["title"]),
        "Symbol": lambda r: rst_math(r["symbol"]),
        "Formula": lambda r: rst_math(r["formula"]),
        "Abstract": lambda r: rst_text(r["abstract"]),
    }
    lines = list_table(rows=read_catalog(name="statistics"), columns=columns)
    (CATALOG_PAGES_DIR / "statistics.rst").write_text("\n".join(lines), encoding="utf-8")

    # flags: a single table, highest value first
    flags = sorted(read_catalog(name="flags"), key=lambda r: -int(r["value"]))
    columns = {
        "Value": lambda r: rst_literal(r["value"]),
        "Name": lambda r: rst_literal(r["name"]),
        "Alias": lambda r: rst_literal(r["alias"]),
        "Meaning": lambda r: rst_text(r["abstract"]),
    }
    lines = list_table(rows=flags, columns=columns)
    (CATALOG_PAGES_DIR / "flags.rst").write_text("\n".join(lines), encoding="utf-8")
    return None


build_catalog_pages()


# REPO PROJECT INFO
# ***********************************************************************
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "plans"
copyright = "2025, Iporã Possantti"
author = "Iporã Possantti"
release = "1.0.0"

# GENERAL CONFIGS
# ***********************************************************************
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Extensions
extensions = [
    # built-in extensions
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    # extra extensions
    # -- LaTeX equations
    "sphinx.ext.mathjax",
    # -- nice copy button for codeblocks
    "sphinx_copybutton",  # install by `python -m pip install sphinx-copybutton`
    # -- converter for markdown files in docs
    "sphinx_design",  # install by `python -m pip install sphinx-design`
    "myst_nb",  # # install by `python -m pip install myst-nb`
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Ignore external dependencies
autodoc_mock_imports = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "warnings",
    "PIL",
    "processing",
    "qgis",
    "osgeo",
    "geopandas",
    "PyPDF2",
    "rasterio",
    "platformdirs",
]

autodoc_member_order = "bysource"

# Exclude the __dict__, __weakref__, and __module__ attributes from being documented
exclude_members = [
    "__dict__",
    "__weakref__",
    "__module__",
    "__str__",
    "__annotations__",
    "__firstlineno__",
]
# Configure autodoc options
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": True,
    "special-members": True,
    "show-inheritance": True,
    "exclude-members": ",".join(exclude_members),
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "figs/*.rst",
    "includes/*.rst",
    "_aux/*.rst",
    "jupyter_execute",
    ".jupyter_cache",
    "generated/catalogs/*",
]

# Jupyter Notebooks variables from myst-nb
nb_execution_mode = "cache"
# enable $...$ and $$...$$ math in markdown cells
myst_enable_extensions = ["dollarmath"]
highlight_language = "python"

# HTML AND THEMES
# ***********************************************************************
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
"""  
Some options for themes  

Built-in:  
>> html_theme = "classic"  
>> html_theme = "alabaster"  
>> html_theme = "bizstyle"  

External (requires installation): 

# PRO TIP: list external themes in pyproject.toml docs dependencies for automatic installation

# by: `python -m pip install sphinx-rtd-theme`   
>> html_theme = "sphinx_rtd_theme" 

# by: `python -m pip install furo`
>> html_theme = "furo"  

# by: `python -m pip install pydata-sphinx-theme`  
>> html_theme = "pydata_sphinx_theme" 

"""
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_logo = (
    "https://github.com/iporepos/plans-assets/blob/main/docs/figs/logo.jpg?raw=true"
)
html_context = {
    # ...
    "default_mode": "light"
}
html_theme_options = {
    "github_url": "https://github.com/iporepos/plans",
    "logo": {
        "text": "plans",
    },
    "navbar_start": ["navbar-logo"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
}
