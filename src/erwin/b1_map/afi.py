import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class AFI(spire.TaskFactory):
    """ Relative B1 map from an AFI sequence.
        
        Reference: Actual flip-angle imaging in the pulsed steady state: A 
        method for rapid three-dimensional mapping of the transmitted 
        radiofrequency field. Yarnykh. Magnetic Resonance in Medicine 57(1).
        2007.
    """
    
    def __init__(
            self, sources: Tuple[str, str], flip_angle: float, tr_ratio: float,
            target: str):
        """ :param sources: Path to the magnitude images
            :param flip_angle: Flip angle (rad)
            :param tr_ratio: Ratio between the two TR
            :param target: Path to the target relative B1 map
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = sources
        self.targets = [target]
        
        self.actions = [(AFI.b1_map, (sources, flip_angle, tr_ratio, target))]
    
    @staticmethod
    def b1_map(sources_path, flip_angle, tr_ratio, target_path):
        images = [nibabel.load(x) for x in sources_path]
        data = [x.get_fdata() for x in images]
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            r = data[1] / data[0]
        n = tr_ratio
        actual_fa = numpy.arccos((r*n - 1)/(n-r))
        
        nibabel.save(
            nibabel.Nifti1Image(actual_fa/flip_angle, image.affine), 
            target_path)
        
def main():
    return entrypoint(AFI)
