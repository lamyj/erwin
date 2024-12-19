import spire

from .. import entrypoint
from ..cli import *

class Tensor(spire.TaskFactory):
    """ Diffusion and optional kurtosis tensor estimation.
        
        This wraps dwi2tensor from MRtrix3.
    """
    
    def __init__(
            self, source: str, target: str, mask: Optional[str]=None,
            dkt: Optional[str]=None, ols: Flag=False, iter: Optional[int]=None,
            b0: Optional[str]=None):
        """ :param source: Path to source diffusion-weighted image
            :param target: Path to target diffusion tensor image
            :param mask: Path to binary mask
            :param dkt: Path to target diffusion kurtosis image
            :param ols: Perform initial fit with OLS
            :param iter: Number of iterative reweightings
            :param b0: Path to target estimated b=0 s/mm² image
        """
        
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        self.targets = [target, *([b0] if b0 else [])]
        self.actions = [
            ["dwi2tensor", "-force"] 
                + (["-mask", mask] if mask else [])
                + (["-dkt", dkt] if dkt else [])
                + (["-ols"] if ols else [])
                + (["-iter", str(iter)] if iter else [])
                + (["-b0", b0] if b0 else [])
                + [source, target]]

def main():
    return entrypoint(Tensor)
