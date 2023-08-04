import itertools
import os

import spire

from .. import entrypoint
from ..cli import *

class SphericalHarmonics(spire.TaskFactory):
    """ Perform multi-shell multi-tissue CSD.
        
        This wraps dwi2fod from MRtrix3.
    """
    
    def __init__(
            self, source: str, response: Tuple[str, ...], target=str,
            mask: Optional[str]=None,
            algorithm: Optional[Choice["csd", "msmt_csd"]]="msmt_csd"):
        """ :param source: Path to the source diffusion-weighted image
            :param response: Path to the single-fiber response file(s)
            :param target: Prefix (msmt_csd) or path (csd) to the harmonics files
            :param mask: Path to the binary mask
        """
        
        spire.TaskFactory.__init__(
            self, str(
                "{}wm.mif.gz".format(target) if algorithm=="msmt_csd"
                else target))
        
        if algorithm == "csd":
            response = (response, )
        self.file_dep = [source, *response]
        if mask is not None:
            self.file_dep.append(mask)
        
        if algorithm == "msmt_csd":
            self.targets = [
                "{}{}.mif.gz".format(target, x) for x in ["wm", "gm", "csf"]]
        else:
            self.targets = [target]
        
        self.actions = [
            ["dwi2fod", "-force", algorithm, source]
                + (["-mask", mask] if mask else [])
                + list(itertools.chain(*zip(response, self.targets)))
        ]

def main():
    return entrypoint(SphericalHarmonics)
