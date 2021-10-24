import gzip
import os

import amico
import nibabel
import numpy
import spire

from .. import entrypoint, parsing
from . import mif_io

class NODDI(spire.TaskFactory):
    """ Fit the NODDI model using AMICO.
        
        References:
        - NODDI: Practical in vivo neurite orientation dispersion and density 
          imaging of the human brain. Zhang et al. NeuroImage 61(4). 2012.
        - Accelerated Microstructure Imaging via Convex Optimization (AMICO) 
          from diffusion MRI data. Daducci et al. NeuroImage 105. 2015.
    """
    
    def __init__(
            self, dwi, response_directory, principal_direction,
            ic_vf, iso_vf, od, 
            mask=None, shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        spire.TaskFactory.__init__(self, str(ic_vf))
        
        model = amico.models.NODDI()
        self.file_dep = (
            [dwi, principal_direction]
            + ([mask] if mask else [])
            + [
                os.path.join(response_directory, "A_{:03}.npy".format(1+x))
                for x in range(1+len(model.IC_ODs)*len(model.IC_VFs))])
        
        self.targets = [ic_vf, iso_vf, od]
        
        self.actions = [
            (NODDI.noddi, (
                dwi, response_directory, principal_direction, ic_vf, iso_vf, od, 
                mask, shell_width, b0_threshold, lmax, ndirs))]
    
    @staticmethod
    def noddi(
            dwi_path, response_directory, principal_direction_path,
            ic_vf_path, iso_vf_path, od_path,  
            mask_path=None, shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        
        amico.core.setup(lmax, ndirs)
        
        scheme = NODDI.amico_scheme(dwi_path, shell_width, b0_threshold)
        
        # Resample the responses to the actual acquisition scheme
        shells, harmonics = amico.lut.aux_structures_resample(scheme, lmax)
        model = amico.models.NODDI()
        model.scheme = scheme
        kernels = model.resample(
            response_directory, shells, harmonics, False, ndirs)
        
        # Prepare all other model parameters
        solver_params = model.set_solver()
        hash_table = amico.lut.load_precomputed_hash_table(ndirs)
        
        # Read the DWI data
        if str(dwi_path).endswith(".gz"):
            fd = gzip.GzipFile(dwi_path)
        else:
            fd = open(dwi_path, "rb")
        dwi_image, _ = mif_io.read(fd)
        fd.close()
        
        principal_direction = nibabel.load(principal_direction_path).get_fdata()
        
        # Prepare the output maps
        maps = numpy.zeros(
            dwi_image.shape[:3]+(len(model.maps_name),), dtype=numpy.float32)
        
        if mask_path:
            mask = numpy.array(nibabel.load(mask_path).dataobj).astype(bool)
        else:
            mask = numpy.full(dwi_image.shape[:-1], True)
        
        # Fit the model in each non-masked voxel
        dwi = dwi_image.get_fdata()
        for index in numpy.ndindex(dwi.shape[:-1]):
            if not mask[index]:
                continue
            
            y = dwi[index]
            # FIXME?
            y[ y < 0 ] = 0
            
            e1 = principal_direction[index]
            
            maps[index], _, _, _ = model.fit(
                y, e1.reshape(-1,3), kernels, solver_params, hash_table)
        
        # Save the NODDI maps
        for name, map in zip(model.maps_name, maps.transpose(3,0,1,2)):
            map_image = nibabel.Nifti1Image(map, dwi_image.affine)
            if name == "ICVF":
                path = ic_vf_path
            elif name == "ISOVF":
                path = iso_vf_path
            elif name == "OD":
                path = od_path
            else:
                print("Skipping {}: unknown map".format(name))
            nibabel.save(map_image, path)
    
    @staticmethod
    def amico_scheme(dwi_path, shell_width=0, b0_threshold=0):
        if str(dwi_path).endswith(".gz"):
            fd = gzip.GzipFile(dwi_path)
        else:
            fd = open(dwi_path, "rb")
        header = mif_io.read_header(fd)
        
        # Amico expects x,y,z (which frame?), b-value (s/mm^2), as MRtrix
        scheme = header[b"dw_scheme"]
        # NOTE Amico expects shelled data
        if shell_width != 0:
            scheme[:,3] = numpy.round(scheme[:,3]/shell_width)*shell_width
        scheme = amico.scheme.Scheme(scheme, b0_threshold)
        return scheme

def main():
    return entrypoint(
        NODDI, [
            ("--dwi", {"help": "Diffusion-weighted image, in MRtrix format"}),
            ("--response-directory", {"help": "NODDI responses directory"}),
            ("--ic-vf", {"help": "Target intra-cellular volume fraction map"}),
            ("--iso-vf", {"help": "Target isotropic volume fraction map"}),
            ("--od", {"help": "Target orientation dispersion map"}),
            parsing.Optional(["--mask", {"help": "Mask image"}]),
            parsing.Optional([
                "--shell-width", {
                    "type":float, "default": 0, 
                    "help": "Width used to group the real b-values in ideal shells"}]),
            parsing.Optional([
                "--b0-threshold", {
                    "type":float, "default": 0, 
                    "help": "Lower b-value threshold"}]),
            parsing.Optional([
                "--lmax", {
                    "type":int, "default": 12,
                    "help": "Maximum order of spherical harmonics"}]),
            parsing.Optional([
                "--ndirs", {
                    "type": int, "default": 32761,
                    "help": "Number of directions on the hemisphere"}])
        ])
