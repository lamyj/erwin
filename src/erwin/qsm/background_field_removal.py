import os

import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class BackgroundFieldRemoval(spire.TaskFactory):
    """ Background field removal using the LBV method of the MEDI toolbox.
        
        Reference: Background field removal by solving the Laplacian boundary
        value problem. Zhou et al. NMR in Biomedicine 27(3). 2014.
    """
    
    def __init__(self, f_total: str, mask: str, target: str):
        """ :param f_total: Path to total field map
            :param mask: Path to binary mask image
            :param target: Path to target object field image
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [f_total, mask]
        self.targets = [target]
        
        self.actions = [(__class__.action, (f_total, mask, target))]
    
    def action(f_total_path, mask_path, target_path):
        import meg
        
        medi_toolbox_path = os.environ["ERWIN_MEDI"]
        f_total_image = nibabel.load(f_total_path)
        mask_image = nibabel.load(mask_path)
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            
            engine["f_total"] = f_total_image.get_fdata()
            engine["mask"] = numpy.array(mask_image.dataobj)
            engine["shape"] = numpy.array(f_total_image.shape[:3], float)
            engine["voxel_size"] = f_total_image.header["pixdim"][1:4]
            
            engine("f_object = LBV(f_total, mask, shape, voxel_size, 0.005);")
            f_object = engine["f_object"]
        
        nibabel.save(
            nibabel.Nifti1Image(f_object, f_total_image.affine), target_path)

def main():
    return entrypoint(BackgroundFieldRemoval)
