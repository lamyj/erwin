# erwin &mdash; a qMRI toolbox

*erwin* is a Python-based toolbox dedicated to the computation of quantitative maps from MRI data. Accessible through either its Python API or its command-line interface, *erwin* provides a unified interface to well-known methods and toolboxes.

- Field mapping: relative B<sub>0</sub> and relative B<sub>1</sub> 
- Cerebral blood flow: <abbr title="Arterial Spin Labelling">ASL</abbr>-based models (pulsed ASL, pseudo-continuous ASL)
- Diffusion: DTI and spherical harmonics, NODDI
- Motion correction
- Magnetization transfer: MTR and single-point qMT
- Magnetic susceptibility: QSM and R<sub>2</sub><sup>*</sup>
- T<sub>1</sub> and T<sub>2</sub> mapping: VFA, bSSFP, pSSFP

Since quantitative MRI requires accessing acquisition parameters, often stored in vendor-specific meta-data, *erwin* includes tools to access meta-data in a vendor-neutral way.

Using doit and Spire, *erwin* allows the definition of complex pipelines with automatic dependency handling.

## Installation

*erwin* requires Python ≥ 3.6 The easiest way to install *erwin* and its dependencies is through [PyPi][] and [pip][]:
```
python3 -m pip install erwin
```

If this fails, you may need to
- adjust the `python3` executable to match your local installation
- install [Cython][]

Using the following methods requires additional dependencies:
- Diffusion tensor and spherical harmonics: [MRtrix][]; conversion from Bruker or Siemens DICOM also requires [Dicomifier][]
- Motion correction: [ANTs][]
- NODDI: [Amico][]
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
erwin b0_map --magnitude /path/to/magnitude.nii.gz --phase /path/to/phase.nii.gz --echo-times 0.01 0.02 --target B0_map.nii.gz
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

**TODO** Sample B0 from program
```python
import erwin
import nibabel

magnitude = nibabel.load("/path/to/magnitude.nii.gz")
phase = nibabel.load("/path/to/phase.nii.gz")

```

**TODO** Sample T2 pipeline

[Amico]: https://github.com/daducci/AMICO
[ANTs]: https://github.com/ANTsX/ANTs
[Cython]: https://cython.org/
[Dicomifier]: https://dicomifier.readthedocs.io/
[MEDI]: http://pre.weill.cornell.edu/mri/pages/qsm.html
[MRtrix]: https://www.mrtrix.org/
[pip]: https://pip.pypa.io/en/stable/
[PyPi]: https://pypi.org/
