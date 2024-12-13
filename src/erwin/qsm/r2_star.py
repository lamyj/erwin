import os

import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class R2Star(spire.TaskFactory):
    """ Compute the R2* map (in Hz)
        
        Reference: Algorithm for fast monoexponential fitting based 
        on Auto-Regression on Linear Operations (ARLO) of data. Pei et al.
        Magnetic Resonance in Medicine 73(2). 2015.
    """
    
    def __init__(
            self, source: str, echo_times: Tuple[float, ...], target: str,
            mask: Optional[str]=None):
        """ :param source: Path to source magnitude image
            :param echo_times: Echo times (s)
            :param target: Path to R2* map (Hz)
            :param mask: Path to binary mask
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [source, *([mask] if mask else [])]
        self.targets = [target]
        self.actions = [(__class__.action, (source, echo_times, target, mask))]
    
    @staticmethod
    def action(source_path, echo_times, target_path, mask):
        import meg
        
        medi_toolbox_path = os.environ["ERWIN_MEDI"]
        source = nibabel.load(source_path)
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            engine["echo_times"] = echo_times
            engine["magnitude"] = source.get_fdata()
            engine("R2_star = arlo(echo_times, magnitude);")
            R2_star = engine["R2_star"]
        
        if mask:
            mask = numpy.array(nibabel.load(mask).dataobj)
            R2_star[mask == 0] = 0
        
        nibabel.save(nibabel.Nifti1Image(R2_star, source.affine), target_path)

def main():
    return entrypoint(R2Star, {"echo_times": "te"})
