import itertools
import json
import re

import nibabel
import numpy
import spire

from .. import entrypoint, misc

class DoubleEcho(spire.TaskFactory):
    """ ΔB₀ map (in Hz) using the phase difference between two echoes.
        
        Reference: "An in vivo automated shimming method taking into account
        shim current constraints". Wen & Jaffer. Magnetic Resonance in Medicine
        34(6), pp. 898-904. 1995. doi:10.1002/mrm.1910340616
    """
    
    def __init__(self, sources, target, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        self.sources = sources
        if meta_data is None:
            self.meta_data = [
                re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        else:
            self.meta_data = meta_data
        
        if len(sources) != 2:
            raise Exception("Expected two images, got {}".format(len(sources)))
        if len(meta_data) != 2:
            raise Exception("Expected two meta-data, got {}".format(len(meta_data)))
        
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
        
        magnitude_indices = misc.search_magnitude(meta_data_array)
        phase_indices = misc.search_phase(meta_data_array)
        
        if len(magnitude_indices) != 1:
            raise Exception(
                "Expected one magnitude image, got {}".format(
                    len(magnitude_indices)))
        if len(phase_indices) != 1:
            raise Exception(
                "Expected one phase image, got {}".format(
                    len(phase_indices)))
        
        # Complex signal for the two echoes
        magnitude = sources[magnitude_indices[0]].get_fdata()
        phase = misc.get_phase_data(
            sources[phase_indices[0]].get_fdata(),
            meta_data_array[phase_indices[0]])
        S = magnitude * numpy.exp(1j*phase)
        
        # Un-normalized, complex, phase difference
        delta_phase = S[..., 1] * S[..., 0].conj()
        # Real phase difference
        delta_phase = numpy.angle(delta_phase)
        
        # Difference between echo times in seconds.
        echo_times = [x[0] for x in meta_data_array[0]["EchoTime"]]
        delta_TE = (echo_times[1] - echo_times[0]) * 1e-3
        
        # ΔB₀ map in Hz
        B0_map = delta_phase / (2*numpy.pi*delta_TE)
        
        nibabel.save(
            nibabel.Nifti1Image(B0_map, sources[0].affine), B0_map_path)

def main():
    return entrypoint(
        DoubleEcho, [
            (
                "sources", {
                    "nargs": 2, 
                    "help": 
                        "Double-echo SPGR images with magnitude and phase "
                        "(in any order)"}),
            ("target", {"help": "Path to the target ΔB₀ map"}),
            (
                "--meta-data", "-m", {
                    "nargs": 2,
                    "help": 
                        "Optional meta-data. If not provided, deduced from the "
                        "source images."})
        ])
