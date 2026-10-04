"""
Configuration file for the Sphinx documentation builder.
Documentation: http://www.sphinx-doc.org/en/master/config
"""  # noqa

# -- Imports -----------------------------------------------------------------

import datetime
import os
import time

# -- Project Information -----------------------------------------------------

project = "novelWriter"
copyright = f"{datetime.date.today().year}"  # noqa: A001

if override_authors := os.environ.get("SPHINX_I18N_AUTHORS"):
    author = override_authors
else:
    author = "Veronica Berglyd Olsen"

if override_version := os.environ.get("SPHINX_I18N_VERSION"):
    release = override_version
else:
    initFile = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "novelwriter", "__init__.py")
    with open(initFile, encoding="utf-8") as inFile:
        for aLine in inFile:
            if aLine.startswith("__version__"):
                release = "20" + aLine.split('"')[1].strip()
                break
        else:
            release = "unknown"

version = release.partition("-")[0]

# -- General Configuration ---------------------------------------------------

os.environ["TZ"] = "Europe/Oslo"
time.tzset()

needs_sphinx = "5.0"
extensions = ["sphinx_design", "sphinx_copybutton"]
templates_path = ["_templates"]
source_suffix = {".rst": "restructuredtext"}
master_doc = "index"
today_fmt = "%A, %d %B %Y at %H:%M"
language = "en"
locale_dirs = ["locales/"]
gettext_compact = False
exclude_patterns = []

# -- Options for HTML Output -------------------------------------------------

html_theme = "sphinx_book_theme"
html_title = f"Version {release}"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "logo": {
        "image_light": "_static/novelwriter-light.png",
        "image_dark": "_static/novelwriter-dark.png",
    },
    "show_toc_level": 2,
    "show_navbar_depth": 1,
    "repository_url": "https://github.com/saga-soft/novelwriter",
    "navigation_with_keys": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "pygments_light_style": "tango",
    "pygments_dark_style": "dracula",
}
html_sidebars = {
    "**": ["navbar-logo", "sidebar-title", "sbt-sidebar-nav"],
}

# -- Options for LaTeX Output ------------------------------------------------

latex_elements = {
    "papersize": "a4paper",
    "pointsize": "11pt",
    "preamble": ("\\usepackage[utf8]{inputenc}\n\\DeclareUnicodeCharacter{2212}{\\textendash}\n"),
    "figure_align": "htbp",
}
latex_logo = "_static/novelwriter-pdf.png"
latex_documents = [(master_doc, "manual.tex", None, author, "manual")]
