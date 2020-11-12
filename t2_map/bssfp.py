import argparse
import base64
import itertools
import json
import re
import warnings

import dicomifier
import nibabel
import numpy
import spire

class bSSFP(spire.TaskFactory):
    """ Compute a map of T2 from bSSFP images
        
        Reference: "Analytical corrections of banding artifacts in driven
        equilibrium single pulse observation of T2 (DESPOT2)". Jutras et al.
        Magnetic Resonance in Medicine 76(6). 2015.
    """
    
    def __init__(self, sources, B1_map, T1_map, T2_map, meta_data=None):
        spire.TaskFactory.__init__(self, T2_map)
        
        self.sources = sources
        
        if meta_data is None:
            meta_data = [
                re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        self.meta_data = meta_data
        
        self.B1_map = B1_map
        self.T1_map = T1_map
        
        self.file_dep = list(itertools.chain(
            sources, meta_data, [B1_map, T1_map]))
        self.targets = [T2_map]
        
        self.actions = [
            (bSSFP.t2_map, (sources, meta_data, B1_map, T1_map, T2_map))]
    
    @staticmethod
    def t2_map(
            source_paths, meta_data_paths, B1_map_path, T1_map_path, 
            T2_map_path):
       
        # Load the meta-data
        meta_data_array = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data_array.append(json.load(fd))
       
        # Reading bSSFP meta data
        FA = numpy.empty(len(meta_data_array)) # [rad]
        TR = numpy.empty(len(meta_data_array)) # [s]
        TE = numpy.empty(len(meta_data_array)) # [s]
        phi = numpy.empty(len(meta_data_array)) # [°]
        for index, meta_data in enumerate(meta_data_array):
            FA[index] = numpy.radians(meta_data['FlipAngle'][0])
            TR[index] = meta_data['RepetitionTime'][0]*1e-3
            TE[index] = meta_data['EchoTime'][0]*1e-3
            phi[index] = bSSFP.get_phase_increment(meta_data)
        
        # Sort images and meta-data according to the pair (ϕ, FA)
        # so that we get (ϕ₁, FA₁), (ϕ₁, FA₂), (ϕ₂, FA₁), (ϕ₂, FA₂), etc.
        for variable in [source_paths, FA, TR, TE, phi]:
            variable[:] = [
                item for item, _, _ in sorted(
                    zip(variable, phi, FA), key=lambda x: (x[-2], x[-1]))]
        
        # Load the images
        sources = [nibabel.load(x) for x in source_paths]
        B1_map = nibabel.load(B1_map_path)
        T1_map = nibabel.load(T1_map_path)
        
        # Clamp the B1 map
        B1 = B1_map.get_fdata()
        B1[B1<0.1] = numpy.nan
        
        S = numpy.asarray([source.get_fdata() for source in sources])
        
        tau = numpy.empty((S.shape[0]//2, )+S.shape[1:])
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            E1 = numpy.exp(-TR[0]/T1_map.get_fdata())
        
        true_FA = numpy.tensordot(FA, B1, axes=((),()))
        tan_FA = numpy.tan(true_FA)
        sin_FA = numpy.sin(true_FA)
        
        for i in range(0, len(S), 2):
            # Terms of eq. 3
            X1 = S[i] / tan_FA[i]
            X2 = S[i+1] / tan_FA[i+1]
            Y1 = S[i] / sin_FA[i]
            Y2 = S[i+1] / sin_FA[i+1]
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Slope of eq. 7
                m = (Y2 - Y1)/(X2 - X1)
                # Log operand of reduced T2, eq. 5
                n = (E1-m) / (1-m*E1)
                tau[i//2] = -TR[0]/numpy.log((E1-m) / (1-m*E1))
        
        # Definition below eq. 11 and in eq. 12
        K_N = numpy.sqrt(8/(3*tau.shape[0]))
        T2 = K_N * numpy.sqrt(numpy.nansum(tau**2, axis=0))
        
        # Clamp the results to avoid large errors outside the object
        T2[T2<0] = 0
        T2[T2>10] = 10
        
        nibabel.save(nibabel.Nifti1Image(T2, sources[0].affine), T2_map_path)
    
    @staticmethod
    def get_phase_increment(meta_data):
        """ Read the phase increment from the private data. """    
        
        csa_group = None
        for key, value in meta_data.items():
            match = re.match(r"(0029)00(\d\d)", key)
            if match:
                if base64.b64decode(value[0]) == b"SIEMENS CSA HEADER":
                    csa_group = (
                        (int(match.group(1), 16) << 16) + 
                        (int(match.group(2), 16) <<  8))
                    break
        if csa_group is None:
            # Default to the usual location
            csa_group = 0x00291000
        
        csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
            base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
        protocol = csa["MrPhoenixProtocol"][0]
        
        phase_increment = float(
            re.search(
                br"^sWiPMemBlock.alFree\[5\]\s*=\s*(\S+)$", protocol, re.M
            ).group(1))
        
        return phase_increment

def main():
    parser = argparse.ArgumentParser(description=bSSFP.__doc__)
    parser.add_argument(
        "sources", nargs="+", help="SPGR images with different flip angles")
    parser.add_argument("B1_map", help="B1 map in SPGR space")
    parser.add_argument("T1_map", help="T1 map in SPGR space")
    parser.add_argument("T2_map", help="Path to the target MPF map")
    arguments = parser.parse_args()
    
    task = bSSFP(**vars(arguments))
    bSSFP.t2_map(
        task.sources, task.meta_data, task.B1_map, task.T1_map, *task.targets)
