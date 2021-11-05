import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class MTR(spire.TaskFactory):
    """ Compute the MT ratio of two images.
        
        The sources images can be supplied in any order, they will be sorted
        before computing the ratio.
    """
    
    def __init__(self, MT_off: str, MT_on: str, target: str):
        """ :param MT_off: Path to image without MT pulse
            :param MT_on: Path to image with MT pulse
            :param target: Path to target MTR map
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [MT_off, MT_on]
        self.targets = [target]
        
        self.actions = [(MTR.mtr_map, (MT_off, MT_on, target))]
    
    @staticmethod
    def mtr_map(MT_off_path, MT_on_path, mtr_map_path):
        MT_off = nibabel.load(MT_off_path)
        MT_on = nibabel.load(MT_on_path)
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            MT_off_array = MT_off.get_fdata()
            MT_on_array = MT_on.get_fdata()
            # If we have multiple echoes, average them
            if MT_on.ndim > 3:
                MT_off_array = MT_off_array.mean(axis=-1)
                MT_on_array = MT_on_array.mean(axis=-1)
            MTR = 1 - MT_on_array / MT_off_array
        
        MTR[MTR<0] = 0
        MTR[MTR>1] = 1
        
        nibabel.save(nibabel.Nifti1Image(MTR, MT_off.affine), mtr_map_path)

def main():
    return entrypoint(MTR, {"MT_off": "mt_off", "MT_on": "mt_on"})
