Welcome to erwin's documentation!
=================================

*erwin* is a Python-based toolbox dedicated to the computation of quantitative maps from MRI data. Accessible through either its Python API or its command-line interface, *erwin* provides a unified interface to well-known methods and toolboxes.

- Field mapping: relative B0 and relative B1 
- Cerebral blood flow: ASL-based models (pulsed ASL, pseudo-continuous ASL)
- Diffusion: DTI and spherical harmonics, NODDI
- Motion correction
- Magnetization transfer: MTR and single-point qMT
- Magnetic susceptibility: QSM and R2*
- T1 and T2 mapping: VFA, bSSFP, pSSFP

Since quantitative MRI requires accessing acquisition parameters, often stored in vendor-specific meta-data, *erwin* includes tools to access meta-data in a vendor-neutral way. Using `doit`_ and `Spire`_, *erwin* allows the definition of complex pipelines with automatic dependency handling.

*erwin* is free software, released under the `MIT license`_, and its source code is available on `GitHub`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   install.rst
   usage.rst
   methods/index.rst

Indices and tables
==================

* :ref:`genindex`

.. _doit: https://pydoit.org/
.. _GitHub: https://github.com/lamyj/erwin/
.. _MIT license: https://en.wikipedia.org/wiki/MIT_License
.. _PyPi: https://pypi.org/
.. _Spire: https://github.com/lamyj/spire
