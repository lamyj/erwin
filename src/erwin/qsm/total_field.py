import json
import os
import re

import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class TotalField(spire.TaskFactory):
    """ Unwrapping and total susceptibility field of the MEDI toolbox.
    """
    
    def __init__(
            self, magnitude: str, phase: str, echo_times: Tuple[float, ...],
            f_total: str, sd_noise: Optional[str]=None,
            phi_0: Optional[str]=None):
        """ :param magnitude: Path to source magnitude images
            :param phase: Path to source phase images
            :param echo_times: Echo times (s)
            :param f_total: Path to target total field image
            :param sd_noise: Path to target map of standard deviation of noise in total susceptibility field
            :param phi_0: Path to target map of phase extrapolated at t=0
        """
        
        spire.TaskFactory.__init__(self, str(f_total))
        
        self.file_dep = [magnitude, phase]
        self.targets = [f_total]
        if sd_noise is not None:
            self.targets.append(sd_noise)
        if phi_0 is not None:
            self.targets.append(phi_0)
        
        self.actions = [(
            __class__.action,
            (magnitude, phase, echo_times, f_total, sd_noise, phi_0))]
    
    def action(magnitude_path, phase_path, echo_times, f_total_path, sd_noise_path, phi_0_path):
        
        import meg
        
        medi_toolbox_path = os.environ["ERWIN_MEDI"]
        magnitude_image = nibabel.load(magnitude_path)
        phase_image = nibabel.load(phase_path)
        signal = magnitude_image.get_fdata() * numpy.exp(-1j*phase_image.get_fdata())
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            
            engine["signal"] = signal
            # MEDI toolbox expects shape as a floating point array
            engine["shape"] = numpy.array(signal.shape[:3], float)
            engine["echo_times"] = echo_times
            
            # Compute the wrapped total field, as γ ΔB ΔTE [rad]
            engine(
                "[f_total, sd_noise, residuals, phi_0] "
                    "= Fit_ppm_complex_TE(signal, echo_times);")
            
            f_total = engine["f_total"]
            sd_noise = engine["sd_noise"]
            phi_0 = engine["phi_0"]
        
        nibabel.save(
            nibabel.Nifti1Image(f_total, magnitude_image.affine), f_total_path)
        if sd_noise_path is not None:
            nibabel.save(
                nibabel.Nifti1Image(sd_noise, magnitude_image.affine), 
                sd_noise_path)
        if phi_0_path is not None:
            print(phi_0_path)
            nibabel.save(
                nibabel.Nifti1Image(phi_0, magnitude_image.affine), phi_0_path)

def main():
    return entrypoint(TotalField, {"echo_times": "te"})
