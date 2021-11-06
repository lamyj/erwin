Installation
============

*erwin* requires Python ≥ 3.7 The easiest way to install *erwin* and its dependencies is through `PyPi`_ and `pip`_: ``python3 -m pip install erwin``

If this fails, you may need to

- adjust the ``python3`` executable to match your local installation
- upgrade ``pip`` (``python3 -m pip install --upgrade pip``, especially on Debian ≤ 10 and Ubuntu ≤ 18.04)
- install `Cython`_ (``apt-get install -y cython3`` on Debian, Ubuntu and other Debian derivatives)
- install BLAS and LAPACK (``apt-get install -y gfortran libblas-dev liblapack-dev`` on Debian, Ubuntu and other Debian derivatives)

Using the following methods requires additional dependencies:

- Diffusion tensor and spherical harmonics: `MRtrix`_; conversion from Bruker or Siemens DICOM also requires `Dicomifier`_
- Motion correction: `ANTs`_
- QSM: `MEDI`_

.. _ANTs: https://github.com/ANTsX/ANTs
.. _Cython: https://cython.org/
.. _Dicomifier: https://dicomifier.readthedocs.io/
.. _MEDI: http://pre.weill.cornell.edu/mri/pages/qsm.html
.. _MRtrix: https://www.mrtrix.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _PyPi: https://pypi.org/
