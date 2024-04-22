"""Configuration file for the Sphinx documentation builder."""

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime
import re
sys.path.insert(0, os.path.abspath(".."))


def find_author_release():
    """Finding package authors and release."""
    with open("../../deforisk_plugin.py", encoding="utf-8") as file:
        file_text = file.read()
    _author = re.search('^__author__\\s*=\\s*"(.*)"',
                        file_text, re.M).group(1)
    _release = re.search('^__version__\\s*=\\s*"(.*)"',
                         file_text, re.M).group(1)
    return (_author, _release)


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "deforisk"
(author, release) = find_author_release()
_today = datetime.date.today()
year = _today.year
copyright = f"{year}, {author}"

# -- Sphynx options ----------------------------------------------------------
add_module_names = False
add_function_parentheses = True

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.viewcode',
              'sphinx.ext.mathjax']

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme_options = {
    "navigation_with_keys": "false",
    "logo": {
        "text": "deforisk Qgis plugin"
    }
}

html_logo = "_static/logo-deforisk.svg"
html_favicon = "_static/favicon.ico"
html_title = ("deforisk — Create and compare deforestation risk maps")
html_short_title = "deforisk"
html_base_url = "https://ecology.ghislainv.fr/deforisk-qgis-plugin/"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

# End Of File
