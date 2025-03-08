import os
import sys

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath(".."))

import orangebox

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_rtd_theme",
]

primary_domain = "py"
default_role = "py:obj"

autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_inherit_docstrings = False

project = "orangebox"
copyright = "The Orangebox Authors"

version = release = orangebox.__version__

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 2,
}
