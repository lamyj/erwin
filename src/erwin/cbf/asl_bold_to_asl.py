import json
import re

import nibabel
import numpy
import spire

from .. import entrypoint

class ASLBOLDToASL(spire.TaskFactory):
    """ Separate ASL signal from ASL-BOLD based on Fourier analysis.
        
        References:
        - Mapping resting-state functional connectivity using perfusion MRI.
          Chuang et al. NeuroImage 40(4). 2008.
        - Brain perfusion in dementia with Lewy bodies and Alzheimer’s disease: 
          an arterial spin labeling MRI study on prodromal and mild dementia 
          stages. Roquet et al. Alzheimer's Research & Therapy 8(1). 2016.
    """
    
    def __init__(self, source, meta_data, target, cutoff_frequency=0.1125):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [source]
        self.targets = [target]
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.actions = [
            (
                ASLBOLDToASL.filter, 
                (source, meta_data, cutoff_frequency, target))]
    
    def filter(source_path, meta_data_path, cutoff_frequency, target_path):
        source = nibabel.load(source_path)
        
        # Get repetition time
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        TR = meta_data["RepetitionTime"][0] * 1e-3
        
        # Build the frequencies array and the stop-band based on the TR
        # NOTE: the first volume does not have the inversion pulses and must not
        # be part of the FFT. Additionnally, for consistency, we keep ω=0. 
        # However, since we are only interested in ΔM when computing the CBF, 
        # this choice does not affect the CBF computation.
        frequencies = numpy.fft.fftfreq(source.shape[3]-1, TR)
        pass_band = numpy.abs(frequencies) >= cutoff_frequency
        pass_band[0] = True
        pass_band = pass_band.astype(float)

        source_fft = numpy.fft.fft(source.get_fdata()[...,1:], axis=-1)
        source_fft *= pass_band

        target_array = source.get_fdata().copy()
        target_array[..., 1:] = numpy.fft.ifft(source_fft, axis=-1).real
        nibabel.save(
            nibabel.Nifti1Image(target_array, source.affine), target_path)

def main():
    return entrypoint(
        ASLBOLDToASL, [
            ("source", {"help": "Source ASL-BOLD image"}),
            ("meta_data", {"nargs": "?", "help": "Source image meta-data"}),
            ("target", {"help": "Target ASL image"}),
            (
                "--cutoff-frequency", 
                {"help": "Cut-off frequency", "type": float, "default": 0.1125})
        ])
