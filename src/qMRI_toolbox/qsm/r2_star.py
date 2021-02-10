import json
import re

import meg
import nibabel
import numpy
import spire

from .. import entrypoint

class R2Star(spire.TaskFactory):
    """ Compute the R2* map (in Hz)
        
        Reference: Algorithm for fast monoexponential fitting based 
        on Auto-Regression on Linear Operations (ARLO) of data. Pei et al.
        Magnetic Resonance in Medicine 73(2). 2015.
    """
    
    def __init__(self, source, target, medi_toolbox, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        
        self.actions = [
            (R2Star.arlo, (source, meta_data, medi_toolbox, target))]
    
    @staticmethod
    def arlo(source_path, meta_data_path, medi_toolbox_path, target_path):
        source = nibabel.load(source_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        echo_times = [x[0]*1e-3 for x in meta_data["EchoTime"]]
        
        with meg.Engine() as engine:
            engine(f"run('{medi_toolbox_path}/MEDI_set_path.m');")
            engine["echo_times"] = echo_times
            engine["magnitude"] = source.get_fdata()
            engine("R2_star = arlo(echo_times, magnitude);")
            R2_star = engine["R2_star"]
        
        nibabel.save(nibabel.Nifti1Image(R2_star, source.affine), target_path)

def main():
    return entrypoint(
        R2Star, [
            ("source", {"help": "Multi-echo magnitude image"}),
            ("target", {"help": "R2* image"}),
            (
                "--medi", {
                    "required": True, 
                    "dest": "medi_toolbox_path", 
                    "help": "Path to the MEDI toolbox"})])
