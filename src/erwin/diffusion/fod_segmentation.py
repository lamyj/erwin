import os
import spire
from .. import entrypoint
from ..cli import *

class FODSegmentation(spire.TaskFactory):
    """ Segmentation of Fibre Orientation Distributions to fixels.
        
        This wraps fod2fixel from MRtrix3.
    """
    
    def __init__(
            self, fod: str, fixel_directory: str, afd: Optional[str]=None,
            peak_amp: Optional[str]=None, disp: Optional[str]=None):
        """ :param fod: Path to FOD image
            :param fixel_directory: Path to target fixel directory
            :param afd: Path to apparent fiber density map
            :param peak_amp: Path to map of the maximal FOD peak
            :param disp: Path to dispersion map
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
