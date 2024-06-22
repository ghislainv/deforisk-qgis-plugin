"""Configuration file for the Sphinx documentation builder."""

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime
import re
from sphinx.builders.html import StandaloneHTMLBuilder

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
(_, release) = find_author_release()
_today = datetime.date.today()
year = _today.year
copyright = f"{year}, Cirad and FAO"

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


StandaloneHTMLBuilder.supported_image_types = [
    "image/svg+xml",
    "image/gif",
    "image/png",
    "image/jpeg",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme_options = {
    "navigation_with_keys": "false",
    "logo": {
        "text": "deforisk QGIS plugin"
    },
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
    "footer_end": ["theme-version"],
    "secondary_sidebar_items": ["page-toc"],
    "navbar_end": ["navbar-icon-links"],
    "icon_links": [
        {"name": "GitHub",
         "url": "https://github.com/ghislainv/deforisk-qgis-plugin",
         "icon": "fa-brands fa-github"},
        {"name": "QGIS",
         "url": "https://www.qgis.org/",
         "icon": "_static/icon_qgis.png",
         "type": "local"},
        {"name": "Cirad",
         "url": "https://www.cirad.fr/en",
         "icon": "_static/icon_cirad.png",
         "type": "local"},
        {"name": "FAO",
         "url": "https://www.fao.org",
         "icon": "_static/logo_fao.png",
         "type": "local"}
    ],
    # alternative way to set github header icons
    # "github_url": "https://github.com/ghislainv/defor-qgis-plugin"
}

html_sidebars = {
    "installation": [],
    "get_started": [],
    "articles": [],
    "articles/*": [],
    "plugin_api": [],
    "contributing/*": []
}

html_context = {
    "github_user": "ghislainv",
    "github_repo": "deforisk-qgis-plugin",
    "github_version": "main",
    "doc_path": "docs",
    "default_mode": "light"
}

html_show_sourcelink = False

html_logo = "_static/logo-deforisk.svg"
html_favicon = "_static/favicon.ico"
html_title = ("deforisk — Create and compare deforestation risk maps")
html_short_title = "deforisk"
html_base_url = "https://ecology.ghislainv.fr/deforisk-qgis-plugin/"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

# End Of File
