import os
import spire
from .. import entrypoint, parsing

class FODSegmentation(spire.TaskFactory):
    """ Segmentation of Fibre Orientation Distributions to fixels.
        
        This wraps fod2fixel from MRtrix3.
    """
    
    def __init__(self, fod, fixel_directory, afd=None, peak_amp=None, disp=None):
        """ :param str fod: Path to FOD image
            :param str fixel_directory: Path to target fixel directory
            :param Optional(str) afd: Path to apparent fiber density map
            :param Optional(str) peak_amp: Path to map of the maximal FOD peak
            :param Optional(str) disp: Path to dispersion map
        """
        
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
    return entrypoint(FODSegmentation)
