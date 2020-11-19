import argparse
import os
import subprocess

import spire

class Preprocessing(spire.TaskFactory):
    """ Preprocess a diffusion-weighted image using MRtrix (denoising, removal 
        of Gibbs artifacts, inhomogeneity distortion correction, correction of 
        intensity bias). The input image should include diffusion-related 
        meta-data (phase-encoding information and diffusion-encoding scheme).
    """
    
    def __init__(self, source, target):
        spire.TaskFactory.__init__(self, target)
        
        temp = "__{}_temp.mif".format(os.path.basename(target))
        temp2 = "__{}_temp2.mif".format(os.path.basename(target))
        
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [
        ["dwidenoise", "-force", source, temp],
        # WARNING: must NOT be stored in the same file
        ["mrdegibbs", "-force", temp, temp2],
        [
            "dwifslpreproc", "-force",
            "-scratch", "dwipreproc.tmp", "-rpe_header", 
            # WARNING: eddy complains that data is not shelled even after using
            # the "ideal" b-values (which we don't).
            "-eddy_options", " --slm=linear --data_is_shelled",
            temp2, temp],
        ["dwibiascorrect", "ants", "-force", temp, target],
        # Clean-up
        ["rm", "-rf", temp, temp2, "dwipreproc.tmp"]
    ]

def main():
    parser = argparse.ArgumentParser(description=Preprocessing.__doc__)
    parser.add_argument("source", help="Diffusion-weighted image")
    parser.add_argument(
        "target", help="Path to the target preprocessed DWI image")
    arguments = parser.parse_args()
    
    task = Preprocessing(**vars(arguments))
    for action in task.actions:
        subprocess.check_call(action)
