# Welcome to qMRI Toolbox

qMRI toolbox is a register of Python scripts used to compute MRI parametric maps.

----
## B0 map


    ./B0_map image_mag.nii.gz img_phase.nii.gz output.nii.gz


----
## B1 map
 
**Based on AFI data**

>*"Actual Flip-Angle Imaging in the Pulsed Steady State: A method for rapid three-dimensional mapping of the transmitted radiofrequency field",  [Yarnykh et al., MRM 2007.](https://onlinelibrary.wiley.com/doi/pdf/10.1002/mrm.21120)*

    ./B1_map_AFI AFI.nii.gz output.nii.gz


**Based on XFL data**

> *"Compute a map of B1 from XFL images; based on validation of a very fast B1-mapping sequence for parallel transmission on a human brain at 7T", Amadon et al., ISMRM 2011.* 

    ./B1_map_XFL XFL.nii.gz output.nii.gz



----
## T1 map

Both are based on 
>*"Rapid combined T1 and T2 mapping using gradient recalled acquisition in the steady state", [Deoni et al., MRM 2003](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.10407).*

**Based on Variable Flip Angle (VFA) datas**

    ./T1_map_VFA VFA_01.nii.gz VFA_02.nii.gz rB1_map.nii.gz output.nii.gz

where

* VFA\_0*.nii.gz, two magnitude images with different flip angles, 
* rB1\_map.nii.gz, B1\_map in the same voxel space as the VFA.

**Based on Magnetization Transfer (MT) datas**

    ./T1_map_MT MT_PDw.nii.gz MT_T1w.nii.gz rB1_map.nii.gz output.nii.gz

where

* MT\_PDw.nii.gz, proton density from MT datas,
* MT\_T1w.nii.gz, T1 weighted from MT datas,
* rB1\_map.nii.gz, B1\_map in the same voxel space as MT datas.

----
## T2 map

**Based on Partially spoiled Steady-State Free Precession (pSSFP)**

> *"Factors controlling T2 mapping from partially spoiled SSFP sequence: Optimization for skeletal muscle characterization", [Sousa et al., MRM 2012](https://www.ncbi.nlm.nih.gov/pubmed/22189505).*

    ./T2_map_pSSFP pSSFP_01.nii.gz pSSFP_02.nii.gz rB1_map.nii.gz output.nii.gz

where

* pSSFP\_0*.nii.gz 
* rB1\_map.nii.gz

**Based on Balanced Steady-State Free Precession (bSSFP)**

> *"Analytical corrections of banding artifacts in driven equilibrium single pulse observation of T2 (DESPOT2)", [Jutras et al., MRM2015](https://onlinelibrary.wiley.com/doi/abs/10.1002/mrm.26074).*

    ./T2_map_TrueFISP trueFISP_01.nii.gz trueFISP_02.nii.gz trueFISP_03.nii.gz trueFISP_04.nii.gz trueFISP_05.nii.gz trueFISP_06.nii.gz trueFISP_07.nii.gz trueFISP_08.nii.gz rB1_map.nii.gz T1_map.nii.gz output.nii.gz

where

* trueFISP\_0*.nii.gz 
* rB1\_map.nii.gz 
* T1\_map.nii.gz 

----
## MPF map

> *"Time-efficient, high-resolution, whole brain three-dimensional macromolecular proton fraction mapping", [Yarnykh, MRM 2015](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4688249/).*

**Based on Gradient Echo (GRE) datas**

    ./MPF_map_GRE GRE_01.nii.gz GRE_02.nii.gz rB0_map.nii.gz rB1_map.nii.gz rT1_map.nii.gz output_MPF.nii.gz output_MTR.nii.gz

where

* GRE\_0*.nii.gz, GRE magnitude image (with and without MT pulse)


**Based on Magnetization Transfer (MT) datas**

    ./MPF_map_MT MT_PDw.nii.gz MT_MTw.nii.gz rB0_map.nii.gz rB1_map.nii.gz rT1_map.nii.gz output_MPF.nii.gz output_MTR.nii.gz

----
## QSM map

Before getting the susceptibility image from QSM datas, they have to be set up via pre-processing scripts.

**Rephase images**

> *"Phase reconstruction from Multiple Coil Data Using a Virtual Reference Coil", [Parker et al, MRM 2014](https://www.ncbi.nlm.nih.gov/pubmed/24006172).*

    ./rephase_images GRE_01.nii.gz GRE_02.nii.gz omag.nii.gz ophase.nii.gz oHvector.bvec ocomb

where

* GRE\_0*.nii.gz, GRE magnitude and phase images (in any order)
* omag.nii.gz, magnitude-4D result
* ophase.nii.gz, phase-4D result
* oHvector.bvec, magnetic field vector result
* ocomb, prefix for combined images


**Unwrap phase images**

    ./unwrap_phase phase4D.nii.gz comb_mag.nii.gz mask.nii.gz output.nii.gz

* comb\_mag.nii.gz, one combined GRE magnitude
* mask.nii.gz, brain mask from the GRE data

Tissue phase estimated result

STI SUITE MATLAB TOOLBOX

**Estimate susceptibility data**

STI SUITE ATLAB TOOLBOX

    ./QSM_map tissue_phase.nii.gz mask.nii.gz GRE.nii.gz H.bvec output.nii.gz

where

* tissue\_phase.nii.gz, result from the previous script, unwrap_phase
* mask.nii.gz, brain mask from the GRE data, the same as used previously
* GRE.nii.gz, one GRE image (magnitude or phase)

----
## R2\*, T2\* & S0 maps

    ./R2star_map magnitude4D.nii.gz mask.nii.gz GRE.nii.gz output_R2.nii.gz output_T2.nii.gz output_S0.nii.gz
where
    
* mask.nii.gz, brain mask from the GRE data, the same as used previously
* GRE.nii.gz, one GRE image (magnitude or phase)

----
## CBF

**Based on Pseudo-Continuous Arterial Spin Labeling (pCASL) datas**

> *"Arterial transit time imaging with flow encoding arterial spin tagging (FEAST)", [Wang et al., MRM 2003](https://onlinelibrary.wiley.com/doi/pdf/10.1002/mrm.10559).*
    
    ./CBF_map pCASL_01.nii.gz pCASL_02.nii.gz M0.nii.gz output.nii.gz

