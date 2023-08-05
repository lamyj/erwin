import spire

from .. import entrypoint
from ..cli import *

class SIFT2(spire.TaskFactory):
    """ Optimise per-streamline cross-section multipliers to match a whole-brain
        tractogram to fixel-wise fibre densities
    """
    
    def __init__(
            self, tracks: str, fod: str, weights: str,
            act: Optional[str]=None, mu: Optional[str]=None):
        """ :param tracks: Path to tracks
            :param fod: Path to spherical harmonics
            :param weights: Target weights file
            :param act: Path to ACT image
            :param mu: Target coefficient file
        """
        
        spire.TaskFactory.__init__(self, str(weights))
        
        self.file_dep = [tracks, fod]
        if act is not None:
            self.file_dep.append(act)
        
        self.targets = [weights]
        if mu is not None:
            self.targets.append(mu)
        
        self.actions =[
            ["tcksift2", "-force", tracks, fod, weights]
                + (["-act", act] if act is not None else [])
                + (["-out_mu", mu] if mu is not None else [])]

def main():
    return entrypoint(SIFT2)
