import argparse
import itertools
import json
import re

import nibabel
import numpy
import spire

class DoubleEcho(spire.TaskFactory):
    """ Compute the ΔB₀ map (in Hz) using the phase difference between two 
        echoes.
        
        Reference: "Automatic field map generation and off-resonance correction
        for projection reconstruction imaging". Nayak & Nishimura. Magnetic 
        Resonance in Medicine 43(1). 2000.
    """
    
    def __init__(self, sources, target):
        spire.TaskFactory.__init__(self, target)
        
        self.sources = sources
        self.meta_data = [
            re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        
        self.file_dep = list(itertools.chain(sources, self.meta_data))
        self.targets = [target]
        
        self.actions = [
            (DoubleEcho.b0_map, (sources, self.meta_data, *self.targets))]
    
    @staticmethod
    def b0_map(source_paths, meta_data_paths, B0_map_path):
        sources = [nibabel.load(x) for x in source_paths]
        
        meta_data_array = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data_array.append(json.load(fd))
        
        # Complex signal for the two echoes
        by_type = {
            m["ImageType"][2]: s for s, m in zip(sources, meta_data_array)}
        phase = by_type["P"].get_fdata() * numpy.pi/4096
        S = by_type["M"].get_fdata() * numpy.exp(1j*phase)
        
        # Un-normalized, complex, phase difference
        delta_phase = S[..., 1] * S[..., 0].conj()
        # Real phase difference
        delta_phase = numpy.angle(delta_phase)
        # numpy.arctan2(
        #     numpy.imag(delta_phase), numpy.real(delta_phase))
        
        # Difference between echo times in seconds.
        echo_times = [x[0] for x in meta_data_array[0]["EchoTime"]]
        delta_TE = (echo_times[1] - echo_times[0]) * 1e-3
        
        # ΔB₀ map in Hz
        B0_map = delta_phase / (2*numpy.pi*delta_TE)
        
        nibabel.save(
            nibabel.Nifti1Image(B0_map, sources[0].affine), B0_map_path)

def main():
    parser = argparse.ArgumentParser(description=DoubleEcho.__doc__)
    parser.add_argument(
        "sources", nargs=2,
        help="Double-echo SPGR images with magnitude and phase (in any order)")
    parser.add_argument("target", help="Path to the target B0 map")
    arguments = parser.parse_args()
    
    task = DoubleEcho(**vars(arguments))
    DoubleEcho.b0_map(task.sources, task.meta_data, *task.targets)
