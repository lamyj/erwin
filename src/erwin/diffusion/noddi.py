import gzip
import os

import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *
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
            self, dwi: str, response_directory: str, principal_direction: str,
            ic_vf: str, iso_vf: str, od: str, 
            mask: Optional[str]=None, shell_width: Optional[float]=0,
            b0_threshold: Optional[float]=0, lmax: Optional[int]=12,
            ndirs: Optional[int]=32761):
        """ :param dwi: Path to diffusion-weighted image, in MRtrix format
            :param response_directory: Path to response directory
            :param principal_direction: Path to principal direction map
            :param ic_vf: Path to target intra-cellular volume fraction map
            :param iso_vf: Path to target isotropic volume fraction map
            :param od: Path to target orientation dispersion map
            :param mask: Path to mask image
            :param shell_width: Width used to group the real b-values in ideal shells (s/mm^2)
            :param b0_threshold: Lower b-value threshold (s/mm^2)
            :param lmax: Maximum order of spherical harmonics
            :param ndirs: Number of directions on the hemisphere
        """
        
        import amico
        
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
        
        import amico
        
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
        import amico
        
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
    return entrypoint(NODDI)
