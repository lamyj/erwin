Usage
=====

*erwin* can be used in two different ways: from the command line, or from Python programs.

Command-line
------------

On the command-line, the main executable is called `erwin`; a list of all methods can be obtained by 

.. code-block:: bash

    erwin --list

The documentation of each individual method is accessed by appending ``--help`` to its name, e.g. 

.. code-block:: bash
    
    erwin b0_map.double_echo --help

Due to the large number of parameters -- input and output paths, flip angles, echo times, imaging frequencies, etc. -- each command line argument is named. Parameters corresponding to physical quantities are expressed in SI units in order to avoid discrepancies between standards: DICOM uses "usual" units, e.g. milliseconds for TR or degrees for flip angles, while BIDS uses seconds for TR, but keeps degrees for flip angles. 

.. code-block:: bash

  erwin b0_map --magnitude /path/to/m1.nii.gz /path/to/m2.nii.gz --phase /path/to/p1.nii.gz /path/to/p2.nii.gz --echo-times 0.01 0.02 --target B0_map.nii.gz

*erwin* includes a generic meta-data reader to facilitate the conversion to SI: from either a DICOM or a JSON file, meta-data can be queried using specific units. A flip angle can be read and converted to radians using one of the two following examples, from a DICOM file or from a BIDS sidecar file:

.. code-block:: bash

  ALPHA=$(erwin meta_data.get -p /path/to/some_file -q FlipAngle -u deg)

The same tool can be used for array-like meta-data (``erwin meta_data.get -p /path/to/file.dcm -q ImageType.0``) or for nested structures, including vendor-specific elements. For example, Siemens-specific meta-data from the sequence card can be queried by

.. code-block:: bash
  
  erwin meta_data.get -p /path/to/some_file -q 00291020.MrPhoenixProtocol.0.sWiPMemBlock.adFree.0

Python program
--------------

Seen from a Python program, all methods defined in *erwin* are task objects and not function. This enables to easily connect steps in a pipeline: in the following example, the T1 mapping requires the output of the B1 mapping. Note that the path to the B1 map is only defined once, and that the maps will only be computed when calling `erwin.run`.

.. code-block:: python
  
  import erwin

  B1_map = erwin.b1_map.AFI(
      ["afi1.nii.gz", "afi2.nii.gz"], afi_flip_angle, afi_tr_ratio, "B1.nii.gz")
  T1_map = erwin.t1_map.VFA(
      ["vfa1.nii.gz", "vfa2.nii.gz"], vfa_flip_angles, vfa_tr, B1_map.target)
  erwin.run([B1_map, T1_map])

Even for such a small pipeline, it is beneficial to automate the ordering of tasks, and to keep track of which ones have already been executed. This is handled by `doit`_ and `Spire`_ -- both requirements of *erwin*, so they should be already installed. By dropping the last instruction (``erwin.run([B1_map, T1_map])``) and storing the following file in e.g. *pipeline.py*, the pipeline can be run by calling ``doit -f pipeline.py``.

.. code-block:: python

  import erwin

  B1_map = erwin.b1_map.AFI(
      "afi.nii.gz", afi_flip_angle, afi_tr_ratio, "B1.nii.gz")
  T1_map = erwin.t1_map.VFA(
      ["vfa1.nii.gz", "vfa2.nii.gz"], vfa_flip_angles, vfa_te, vfa_tr, 
      B1_map.target, "T1_map.nii.gz")

Note that re-running doit will not re-run the tasks: since neither the original images nor the code have been modified, everything is up-to-date. Refer to the `doit`_ documentation for more details about running tasks.

The complete API is available in the :doc:`documentation<methods/index>`.

.. _doit: https://pydoit.org/
.. _Spire: https://github.com/lamyj/spire
