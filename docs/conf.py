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

for flat layout 
myrepo/  
├──myrepo/  
│   ├── __init__.py  
│   └── module.py  
└── docs/  
use >> sys.path.insert(0, os.path.abspath(".."))  

"""
sys.path.insert(0, os.path.abspath("../src"))  # src layout
# sys.path.insert(0, os.path.abspath(".."))   # flat layout


# REPO PROJECT INFO
# ***********************************************************************
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "plans"
copyright = "2023, Iporã Possantti"
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
    # -- nice copy button for codeblocks
    "sphinx_copybutton",  # install by `python -m pip install sphinx-copybutton`
    # -- converter for markdown files in docs
    "myst_parser",  # install by `python -m pip install myst-parser`
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
]

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
html_theme = "pydata_sphinx_theme"  # <-- [CHECK THIS] it might be not installed. use built-in 'classic' in case
html_static_path = ["_static"]
