import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class TimeToRate(spire.TaskFactory):
    """ Convert a relaxation time to a relaxation rate.
    """
    
    def __init__(
            self, source: str, destination: str,
            range: Optional[Tuple[float, float]]=None):
        """ :param source: Path to source time map (s)
            :param destination: Path to destination rate map (Hz)
            :param range: Rate range outside which the result is clipped (Hz)
        """
        spire.TaskFactory.__init__(self, str(destination))
        
        self.file_dep = [source]
        self.targets = [destination]
        self.actions = [(TimeToRate.invert, (source, range, destination))]
        
    @staticmethod
    def invert(source, range, destination):
        time_image = nibabel.load(source)
        rate_array = 1./time_image.get_fdata()
        if range is not None:
            rate_array = numpy.clip(rate_array, *range)
        nibabel.save(
            nibabel.Nifti1Image(rate_array, time_image.affine), destination)

def main():
    return entrypoint(TimeToRate)
