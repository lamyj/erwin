import os

import spire

from .. import entrypoint

class Ants(spire.TaskFactory):
    """ ANTs-base motion correction.
    """
    
    def __init__(self, source, prefix):
        spire.TaskFactory.__init__(self, str(prefix))
        
        self.file_dep = [source]
        self.targets = [
            "{}{}".format(prefix, suffix) 
            for suffix in [
                ".nii.gz", "MOCOparams.csv", 
                "Warp.nii.gz", "InverseWarp.nii.gz"]]
        
        temp = os.path.join(
            os.path.dirname(prefix), 
            "__{}_temp.nii".format(os.path.basename(prefix)))
        
        # From github:ANTsX/ANTsR/R/ants_motion_estimation.R, `intraSubjectBOLD`
        # settings
        # NOTE: the MoCo-ed mean image is not saved.
        self.actions = [
            ["antsMotionCorr", "-d", "3", "-a", source, "-o", temp],
            [
                "antsMotionCorr", "-d", "3",
                "-o", "[{},{}]".format(prefix, self.targets[0]),
                "--metric", "MI[{},{},1,20,Regular,0.2]".format(
                    temp, source),
                "--transform", "Affine[0.25]", 
                "--iterations", "50x20", "--smoothingSigmas", "1x0", 
                    "--shrinkFactors", "2x1",
                "--useFixedReferenceImage", "1", "--useScalesEstimator", "1", 
                "--n-images", "10", "--use-estimate-learning-rate-once", "1",
                "--write-displacement", "1"],
            ["rm", "-rf", temp]]

def main():
    return entrypoint(
        Ants, [
            ("--source", {"help": "Source time-series image"}),
            ("--prefix", {"help": "Prefix of the target response files"}),
        ])
