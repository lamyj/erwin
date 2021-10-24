import os
import spire
from .. import entrypoint, parsing

class FODSegmentation(spire.TaskFactory):
    """ Segmentation of Fibre Orientation Distributions to fixels.
        
        This wraps fod2fixel from MRtrix3.
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
            ("--fod", {"help": "FOD image"}),
            ("--fixel-directory", {"help": "Target fixel directory"}),
            parsing.Optional(["--afd", {"help": "Apparent fiber density map"}]),
            parsing.Optional(
                ["--peak-amp", {"help": "Map of the maximal FOD peak"}]),
            parsing.Optional(["--disp", {"help": "Dispersion map"}])])
