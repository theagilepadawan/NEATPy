# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
#import sphinx_readable_theme
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('../NEATpy'))


# -- Project information -----------------------------------------------------

project = 'NEATpy'
copyright = '2020, Michael Gundersen'
author = 'Michael Gundersen'

# The full version, including alpha/beta/rc tags
release = '0.0.1'



# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.coverage', "sphinx_rtd_theme", 'sphinx_autodoc_typehints']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'

## CUSTOM
 #THEME 1
#html_theme_path = [sphinx_readable_theme.get_html_theme_path()]
#html_theme = 'readable'

# THEME 2
html_theme = "sphinx_rtd_theme"
## CUSOTM END

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_mock_imports = ["neat", "utils"]
autodoc_typehints = 'description'
autoclass_content = 'init'
add_module_names = False
html_logo = "../documentation/logo.png"



def autodoc_skip_member(app, what, name, obj, skip, options):
    exclusions = ('neat', '__neat__')
    exclude = name in exclusions
    return skip or exclude


def autodoc_process_signature(app, what, name, obj, options, signature, return_annotation):
    if signature and "(preconnection, connection_type, listener=None, parent=None)" in signature:

        return "", return_annotation
    else:
        return signature, return_annotation


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
    app.connect('autodoc-process-signature', autodoc_process_signature)
