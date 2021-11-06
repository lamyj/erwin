# erwin &mdash; a qMRI toolbox

*erwin* is a Python-based toolbox dedicated to the computation of quantitative maps from MRI data. Accessible through either its Python API or its command-line interface, *erwin* provides a unified interface to well-known methods and toolboxes.

- Field mapping: relative B0 and relative B1 
- Cerebral blood flow: ASL-based models (pulsed ASL, pseudo-continuous ASL)
- Diffusion: DTI and spherical harmonics, NODDI
- Motion correction
- Magnetization transfer: MTR and single-point qMT
- Magnetic susceptibility: QSM and R2*
- T1 and T2 mapping: VFA, bSSFP, pSSFP

Since quantitative MRI requires accessing acquisition parameters, often stored in vendor-specific meta-data, *erwin* includes tools to access meta-data in a vendor-neutral way. Using [doit][] and [Spire][], *erwin* allows the definition of complex pipelines with automatic dependency handling.

The complete documentation is available [online](https://erwin.readthedocs.io/).

## Installation

*erwin* requires Python ≥ 3.7 The easiest way to install *erwin* and its dependencies is through [PyPi][] and [pip][]:
```
python3 -m pip install erwin
```

If this fails, you may need to
- adjust the `python3` executable to match your local installation
- upgrade `pip` (`python3 -m pip install --upgrade pip`, especially on Debian ≤ 10 and Ubuntu ≤ 18.04)
- install [Cython][]
- install BLAS and LAPACK 

Using the following methods requires additional dependencies:
- Diffusion tensor and spherical harmonics: [MRtrix][]; conversion from Bruker or Siemens DICOM also requires [Dicomifier][]
- Motion correction: [ANTs][]
- QSM: [MEDI][]

## Command-line usage

On the command-line, the main executable is called `erwin`; a list of all methods can be obtained by 
```shell
erwin --list
```

The documentation of each individual method is accessed by appending `--help` to its name, e.g. 
```shell
erwin b0_map.double_echo --help
```

Due to the large number of parameters -- input and output paths, flip angles, echo times, imaging frequencies, etc. -- each command line argument is named. Parameters corresponding to physical quantities are expressed in SI units in order to avoid discrepancies between standards: DICOM uses "usual" units, e.g. milliseconds for TR or degrees for flip angles, while BIDS uses seconds for TR, but keeps degrees for flip angles. 

```shell
erwin b0_map --magnitude /path/to/m1.nii.gz /path/to/m2.nii.gz --phase /path/to/p1.nii.gz /path/to/p2.nii.gz --echo-times 0.01 0.02 --target B0_map.nii.gz
```

*erwin* includes a generic meta-data reader to facilitate the conversion to SI: from either a DICOM or a JSON file, meta-data can be queried using specific units. A flip angle can be read and converted to radians using one of the two following examples, from a DICOM file or from a BIDS sidecar file:

```shell
ALPHA=$(erwin meta_data.get -p /path/to/some_file -q FlipAngle -u deg)
```

The same tool can be used for array-like meta-data (`erwin meta_data.get -p /path/to/file.dcm -q ImageType.0`) or for nested structures, including vendor-specific elements. For example, Siemens-specific meta-data from the sequence card can be queried by

```shell
erwin meta_data.get -p /path/to/some_file -q 00291020.MrPhoenixProtocol.0.sWiPMemBlock.adFree.0
```

## Usage in a Python program

Seen from a Python program, all methods defined in *erwin* are task objects and not function. This enables to easily connect steps in a pipeline: in the following example, the T1 mapping requires the output of the B1 mapping. Note that the path to the B1 map is only defined once, and that the maps will only be computed when calling `erwin.run`.

```python
import erwin

B1_map = erwin.b1_map.AFI(
    ["afi1.nii.gz", "afi2.nii.gz"], afi_flip_angle, afi_tr_ratio, "B1.nii.gz")
T1_map = erwin.t1_map.VFA(
    ["vfa1.nii.gz", "vfa2.nii.gz"], vfa_flip_angles, vfa_tr, B1_map.target)
erwin.run([B1_map, T1_map])
```

Even for such a small pipeline, it is beneficial to automate the ordering of tasks, and to keep track of which ones have already been executed. This is handled by [doit][] and [Spire][] -- both requirements of *erwin*, so they should be already installed. By dropping the last instruction (`erwin.run([B1_map, T1_map])`) and storing the following file in e.g. *pipeline.py*, the pipeline can be run by calling `doit -f pipeline.py`.
```python
import erwin

B1_map = erwin.b1_map.AFI(
    "afi.nii.gz", afi_flip_angle, afi_tr_ratio, "B1.nii.gz")
T1_map = erwin.t1_map.VFA(
    ["vfa1.nii.gz", "vfa2.nii.gz"], vfa_flip_angles, vfa_te, vfa_tr, 
    B1_map.target, "T1_map.nii.gz")
```

Note that re-running doit will not re-run the tasks: since neither the original images nor the code have been modified, everything is up-to-date. Refer to the [doit][] documentation for more details about running tasks.

The complete API is available in the [main documentation](https://erwin.readthedocs.io).

[ANTs]: https://github.com/ANTsX/ANTs
[Cython]: https://cython.org/
[Dicomifier]: https://dicomifier.readthedocs.io/
[doit]: https://pydoit.org/
[MEDI]: http://pre.weill.cornell.edu/mri/pages/qsm.html
[MRtrix]: https://www.mrtrix.org/
[pip]: https://pip.pypa.io/en/stable/
[PyPi]: https://pypi.org/
[spire]: https://github.com/lamyj/spire
