import itertools

import spire

from .. import entrypoint
from ..cli import *

class SphericalHarmonics(spire.TaskFactory):
    """ Perform multi-shell multi-tissue CSD.
        
        This wraps dwi2fod msmt_csd from MRtrix3.
    """
    
    def __init__(
            self, source: str, global_response: Tuple[str, ...], prefix=str,
            mask: Optional[str]=None):
        """ :param source: Path to the source diffusion-weighted image
            :param global_response: Path to the single-fiber response files
            :param prefix: Prefix of the target harmonics files
            :param mask: Path to the binary mask
        """
        
        spire.TaskFactory.__init__(self, prefix+"*.mif.gz")
        
        self.file_dep = [source, *global_response]
        if mask is not None:
            self.file_dep.append(mask)
        
        self.targets = [
            "{}{}.mif.gz".format(prefix, x) for x in ["wm", "gm", "csf"]]
        
        self.actions = [
            ["dwi2fod", "-force", "msmt_csd", source]
                + (["-mask", mask] if mask else [])
                + list(itertools.chain(*zip(global_response, self.targets)))
        ]

def main():
    return entrypoint(SphericalHarmonics)
