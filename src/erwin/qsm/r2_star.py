import nibabel
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
            medi_toolbox: str):
        """ :param source: Path to source magnitude image
            :param echo_times: Echo times (s)
            :param target: Path to R2* map (Hz)
            :param medi_toolbox: Path to the MEDI toolbox
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [source]
        self.targets = [target]
        
        self.actions = [
            (R2Star.arlo, (source, echo_times, medi_toolbox, target))]
    
    @staticmethod
    def arlo(source_path, echo_times, medi_toolbox_path, target_path):
        import meg
        
        source = nibabel.load(source_path)
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            engine["echo_times"] = echo_times
            engine["magnitude"] = source.get_fdata()
            engine("R2_star = arlo(echo_times, magnitude);")
            R2_star = engine["R2_star"]
        
        nibabel.save(nibabel.Nifti1Image(R2_star, source.affine), target_path)

def main():
    return entrypoint(R2Star, {"echo_times": "te", "medi_toolbox": "medi"})
