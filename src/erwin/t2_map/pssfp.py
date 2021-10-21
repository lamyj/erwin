import base64
import itertools
import json
import re

import dicomifier
import nibabel
import numpy
import spire
from sycomore.units import *

from .. import entrypoint, misc

class pSSFP(spire.TaskFactory):
    """ Compute a map of T2 from pSSFP images.
        
        References:
        - Factors controlling T2 mapping from partially spoiled SSFP sequence: 
          Optimization for skeletal muscle characterization. L. de Sousa et al.
          Magnetic Resonance in Medicine 67(5). 2012.
        - Steady state of gradient echo sequences with radiofrequency phase 
          cycling: Analytical solution, contrast enhancement with partial
          spoiling. Ganter. Magnetic Resonance in Medicine 55(1). 2006.
    """
    
    def __init__(self, sources, B1_map, T1_map, T2_map, meta_data=None):
        spire.TaskFactory.__init__(self, str(T2_map))
        
        if meta_data is None:
            meta_data = [
                re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        
        try:
            global_T1 = float(T1_map)
        except ValueError:
            global_T1 = None
        
        self.file_dep = list(itertools.chain(sources, meta_data, [B1_map]))
        if not global_T1:
            self.file_dep.append(T1_map)
        self.targets = [T2_map]
        
        self.actions = [
            (
                pSSFP.t2_map, (
                    sources, meta_data, B1_map, 
                    global_T1 if global_T1 else T1_map, T2_map))]
    
    @staticmethod
    def t2_map(
            source_paths, meta_data_paths, B1_map_path, T1, 
            T2_map_path):

        sources = [nibabel.load(x) for x in source_paths]
        meta_data = [json.load(open(x)) for x in meta_data_paths]
        B1 = nibabel.load(B1_map_path).get_fdata()

        alpha = (meta_data[0]["FlipAngle"][0]*deg).magnitude
        alpha *= B1
        
        TR = (meta_data[0]["RepetitionTime"][0]*ms).magnitude
        
        if not isinstance(T1, float):
            T1 = nibabel.load(T1).get_fdata()

        phi = [None, None]
        for index, item in enumerate(meta_data):
            csa_group = misc.siemens_csa.find_csa_group(item)
            csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
                base64.b64decode(item["{:08x}".format(csa_group+0x20)][0]))
            protocol = csa["MrPhoenixProtocol"][0]
            phase_increment = float(
                re.search(
                        br"sWiPMemBlock.alFree\[5\]\s*=\s*(\S+)$", protocol, re.M
                    ).group(1))
            phi[index] = (phase_increment*deg).magnitude

        S = [x.get_fdata() for x in sources]
        S_sq = numpy.power(S, 2)

        eta = 0.5*(1+numpy.cos(alpha))/(1-numpy.cos(alpha))
        xi = pSSFP.compute_xi(eta)
        
        T2_biased = (
            2*TR/xi * numpy.sqrt(
                (S_sq[0]-S_sq[1]) 
                / (S_sq[1]*phi[1]**2 - S_sq[0]*phi[0]**2)))
        T2 = T2_biased / (1 - 3/2*(eta * T2_biased / T1))

        nibabel.save(nibabel.Nifti1Image(T2, sources[0].affine), T2_map_path)

    @staticmethod
    def compute_xi(eta, N=20):
        """ Compute the ξ factor of Ganter's paper (Eq. 34) given η and the 
            order of the continued fraction.
            
            The default order of the continued fraction (N=20) yields less than 
            1% difference with a very high-order evaluation (N=1_000_000) for 
            all flip angles larger than 5°. 
            
            Note that the values given in table 1 of Ganter's paper are those
            for ξ₀/180*π if we follow the definition of Eq. 34. This correction
            factor is due to the that the phase step increment ϕ is expressed
            in degrees. This function returns the _uncorrected_ value.
        """
        
        xi = (2*(N+1) + 1)*(eta + 1)
        for k in range(N, -1, -1):
            xi = (2*k + 1)*(eta + 1) - (eta * (k+1))**2 / xi
        return xi

def main():
    return entrypoint(
        pSSFP, [
            (
                "sources", {
                    "nargs": "+", "metavar": "source",
                    "help": "pSSFP images with different phase steps increments"}),
            ("B1_map", {"help": "B1 map in pSSFP space"}),
            ("T1_map", {"help": "T1 map in pSSFP space or global T1 in s"}),
            ("T2_map", {"help": "Path to the target T2 map"})])
