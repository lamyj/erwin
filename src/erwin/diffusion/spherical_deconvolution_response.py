import spire

from .. import entrypoint
from ..cli import *

class SphericalDeconvolutionResponse(spire.TaskFactory):
    """ Estimation of WM, GM and CSF response functions.
        
        This wraps "dwi2response dhollander" from MRtrix3.
    """
    
    def __init__(self, source: str, prefix: str, mask: Optional[str]=None):
        """ :param source: Path to the source diffusion-weighted image
            :param prefix: Prefix of the targets response files
            :param mask: Path to the binary mask
        """
        
        spire.TaskFactory.__init__(self, prefix+"*.response")
        
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        
        self.targets = [
            "{}{}.response".format(prefix, x) for x in ["wm", "gm", "csf"]]
        
        self.actions = [
            # DWI-based response estimation
            # As of Mrtrix 3.0.0, this is the "improved" Dhollander method.
            ["dwi2response", "dhollander", "-force"]
                + [source] + (["-mask", mask] if mask else []) + self.targets]

def main():
    return entrypoint(SphericalDeconvolutionResponse)
