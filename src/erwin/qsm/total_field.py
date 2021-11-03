import json
import re

import nibabel
import numpy
import spire

from .. import entrypoint

class TotalField(spire.TaskFactory):
    """ Unwrapping and total susceptibility field of the MEDI toolbox.
    """
    
    def __init__(self, magnitude, phase, f_total, medi_toolbox, sd_noise=None):
        """ :param str magnitude: Path to source magnitude images
            :param str phase: Path to source phase images
            :param str f_total: Path to target total field image
            :param str medi_toolbox,medi: Path to the MEDI toolbox
            :param Optional(str) sd_noise: Path to target map of standard \
                deviation of noise in total susceptibility field
        """
        
        spire.TaskFactory.__init__(self, str(f_total))
        
        self.file_dep = [magnitude, phase]
        self.targets = [f_total]
        if sd_noise is not None:
            self.targets.append(sd_noise)
        
        self.actions = [
            (
                TotalField.total_field, (
                    magnitude, phase, medi_toolbox, f_total, sd_noise))]
    
    def total_field(
            magnitude_path, phase_path, medi_toolbox_path, f_total_path,
            sd_noise_path):
        
        import meg
        
        magnitude_image = nibabel.load(magnitude_path)
        phase_image = nibabel.load(phase_path)
        signal = magnitude_image.get_fdata() * numpy.exp(-1j*phase_image.get_fdata())
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            
            engine["signal"] = signal
            # MEDI toolbox expects shape as a floating point array
            engine["shape"] = numpy.array(signal.shape[:3], float)
            
            # Compute the wrapped total field, as γ ΔB ΔTE [rad]
            engine("[f_total_wrapped, sd_noise] = Fit_ppm_complex(signal);")
            
            # Unwrap the total field
            engine("magnitude = sqrt(sum(abs(signal).^2, 4));")
            engine("f_total = unwrapPhase(magnitude, f_total_wrapped, shape);")
            f_total = engine["f_total"]
            sd_noise = engine["sd_noise"]
        
        nibabel.save(
            nibabel.Nifti1Image(f_total, magnitude_image.affine), f_total_path)
        if sd_noise_path is not None:
            nibabel.save(
                nibabel.Nifti1Image(sd_noise, magnitude_image.affine), 
                sd_noise_path)

def main():
    return entrypoint(TotalField)
