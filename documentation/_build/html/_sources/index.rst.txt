.. NEATpy documentation master file, created by
   sphinx-quickstart on Sat Feb 29 18:59:34 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Master thesis documentation
***********************************

This is the documentation for NEATpy: a transport system conforming to the specification of a transport system
specified by the `TAPS WG`_. It implementation is based on version 4 and 5 of the interface draft. While written in Python,
it utilizes the NEAT_ codebase with the help of language bindings created by SWIG_. In this way this transport system
is logically divided in a front-end and back-end; the Python front-end presents a standards conforming API to the end user,
while under the hood, it uses NEAT to handle all protocol machinery.

.. _TAPS WG: https://github.com/ietf-tapswg/api-drafts
.. _SWIG: http://www.swig.org/
.. _NEAT: https://www.neat-project.org/

.. toctree::
   :caption: API documentation
   :maxdepth: 3

   subdir/API

.. toctree::
   :caption: Simple examples
   :maxdepth: 1

   subdir/Example server
   subdir/Example client


