import os
import spire
from .. import entrypoint

class FODSegmentation(spire.TaskFactory):
    """ Perform segmentation of continuous Fibre Orientation Distributions 
        (FODs) to produce discrete fixels (fod2fixel from MRtrix3).
    """
    
    def __init__(self, fod, fixel_directory, afd=None, peak_amp=None, disp=None):
        spire.TaskFactory.__init__(self, str(fixel_directory))
        self.file_dep = [fod]
        
        self.targets = [
            os.path.join(fixel_directory, "index.mif"),
            os.path.join(fixel_directory, "directions.mif")]
        for value in [afd, peak_amp, disp]:
            if value is not None:
                os.path.join(fixel_directory, value)
        
        self.actions = [
            ["rm", "-rf", fixel_directory],
            ["fod2fixel", "-force"]
                + (["-afd", afd] if afd else [])
                + (["-peak_amp", peak_amp] if peak_amp else [])
                + (["-disp", disp] if disp else [])
                + [fod, fixel_directory]]

def main():
    return entrypoint(
        FODSegmentation, [
            ("fod", {"help": "FOD image"}),
            ("fixel_directory", {"help": "Target fixel directory"}),
            ("--afd", {"help": "Apparent fiber density map"}),
            ("--peak-amp", {"help": "Map of the maximal FOD peak"}),
            ("--disp", {"help": "Dispersion map"})])
