import os
import re

project = "erwin"
copyright = "2021, Université de Strasbourg-CNRS"
author = "J. Lamy, M. Mondino, P. Loureiro de Sousa"
# The short X.Y version
here = os.path.abspath(os.path.dirname(__file__))

version="1.0.0rc2",
with open(os.path.join(here, "..", "setup.py")) as fd:
    version = re.search(r'version="(.+?)"', fd.read())
if not version:
    raise Exception("Could not get version from setup.py")
version = version.group(1)
# The full version, including alpha/beta/rc tags
release = version

extensions = [
    "sphinx.ext.autodoc"
]

autoclass_content = "both"
autodoc_typehints = "description"

templates_path = ["_templates"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
