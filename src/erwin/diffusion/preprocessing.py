import pathlib
import subprocess
import tempfile

import spire

from .. import entrypoint
from ..cli import *

class Preprocessing(spire.TaskFactory):
    """ Preprocess a diffusion-weighted image using MRtrix.
    
        This includes denoising, removal of Gibbs artifacts, inhomogeneity 
        distortion correction, and correction of intensity bias. The input
        image should include diffusion-related meta-data (phase-encoding
        information and diffusion-encoding scheme).
    """
    
    def __init__(
            self, source: str, target: str,
            no_preprocess: Flag=False, no_bias_correction: Flag=False):
        """ :param source: Path to source diffusion-weighted image
            :param target: Path to the target preprocessed DWI image
            :param no_preprocess: Skip Eddy/Topup
            :param no_bias_correction: Skip bias correction
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [
            (
                Preprocessing.preprocess,
                (source, target, no_preprocess, no_bias_correction))]
    
    @staticmethod
    def preprocess(source, target, no_preprocess, no_bias_correction):
        with tempfile.TemporaryDirectory() as dir:
            dir = pathlib.Path(dir)
            
            denoised = dir/"denoised.mif"
            subprocess.check_call(["dwidenoise", "-force", source, denoised])
            
            if no_preprocess and no_bias_correction:
                degibbsed = target
            else:
                degibbsed = dir/"degibbsed.mif"
            # WARNING: must NOT be stored in the same file
            subprocess.check_call(["mrdegibbs", "-force", denoised, degibbsed])
            
            if no_bias_correction:
                preprocessed = target
            else:
                preprocessed = dir/"preprocessed.mif"
            if not no_preprocess:
                subprocess.check_call([
                    "dwifslpreproc", "-force",
                    "-scratch", dir, "-rpe_header", 
                    # WARNING: eddy complains that data is not shelled even
                    # after using the "ideal" b-values (which we don't).
                    "-eddy_options", " --slm=linear --data_is_shelled",
                    degibbsed, preprocessed])
            else:
                preprocessed = degibbsed 
            
            if not no_bias_correction:
                subprocess.check_call([
                    "dwibiascorrect", "ants", "-force", preprocessed, target])

def main():
    return entrypoint(Preprocessing)
