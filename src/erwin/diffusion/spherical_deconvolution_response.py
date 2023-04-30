import spire

from .. import entrypoint
from ..cli import *

class SphericalDeconvolutionResponse(spire.TaskFactory):
    """ Estimation of WM, GM and CSF response functions.
        
        This wraps dwi2response from MRtrix3.
    """
    
    def __init__(
            self, source: str, target: str, mask: Optional[str]=None,
            algorithm: Optional[Choice["tournier", "dhollander"]]="dhollander"):
        """ :param source: Path to the source diffusion-weighted image
            :param target: Prefix (dhollander) or path (tournier) to the response
            :param mask: Path to the binary mask
            :param algorithm: Name of the estimation algorithm 
        """
        
        spire.TaskFactory.__init__(
            self,
            str(target+"wm.response" if algorithm=="dhollander" else target))
        
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        
        if algorithm == "dhollander":
            self.targets = [
                "{}{}.response".format(target, x) for x in ["wm", "gm", "csf"]]
        else:
            self.targets = [target]
        
        self.actions = [
            ["dwi2response", algorithm, "-force"]
                + [source] + (["-mask", mask] if mask else []) + self.targets]

def main():
    return entrypoint(SphericalDeconvolutionResponse)
