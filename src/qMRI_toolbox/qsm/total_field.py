import json
import re

import meg
import nibabel
import numpy
import spire

from .. import entrypoint

class TotalField(spire.TaskFactory):
    """ Compute the unwrapped total susceptibility field
    """
    
    def __init__(self, magnitude, phase, target, medi_toolbox, phase_meta_data=None):
        spire.TaskFactory.__init__(self, target)
        
        if phase_meta_data is None:
            phase_meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(phase))
        
        self.file_dep = [magnitude, phase, phase_meta_data]
        self.targets = [target]
        
        
        self.actions = [
            (
                TotalField.total_field, 
                (magnitude, phase, phase_meta_data, medi_toolbox, target))]
    
    def total_field(
            magnitude_path, phase_path, phase_meta_data_path, 
            medi_toolbox_path, target_path):
        magnitude_image = nibabel.load(magnitude_path)
        phase_image = nibabel.load(phase_path)
        
        try:
            with open(phase_meta_data_path) as fd:
                phase_meta_data = json.load(fd)
        except FileNotFoundError:
            phase_meta_data = None
        
        phase = phase_image.get_fdata()
        if (
                phase_meta_data is not None
                and phase_meta_data["ImageType"][2] == "P" 
                and phase_meta_data["Manufacturer"][0] == "SIEMENS"):
            phase *= numpy.pi / 4096
        
        signal = magnitude_image.get_fdata() * numpy.exp(-1j*phase)
        
        with meg.Engine() as engine:
            engine(f"run('{medi_toolbox_path}/MEDI_set_path.m');")
            
            engine["signal"] = signal
            # MEDI toolbox expects shape as a floating point array
            engine["shape"] = numpy.array(signal.shape[:3], float)
            
            # Compute the wrapped total field, as γ ΔB ΔTE [rad]
            engine("[f_total_wrapped, sd_noise] = Fit_ppm_complex(signal);")
            
            # Unwrap the total field
            engine("magnitude = sqrt(sum(abs(signal).^2, 4));")
            engine("f_total = unwrapPhase(magnitude, f_total_wrapped, shape);")
            f_total = engine["f_total"]
        
        nibabel.save(
            nibabel.Nifti1Image(f_total, magnitude_image.affine), target_path)

def main():
    return entrypoint(
        TotalField, [
            ("magnitude", {"help": "Multi-echo magnitude image"}),
            ("phase", {"help": "Multi-echo phase image"}),
            ("target", {"help": "Total field image"}),
            (
                "--medi", {
                    "required": True, 
                    "dest": "medi_toolbox", 
                    "help": "Path to the MEDI toolbox"})])
