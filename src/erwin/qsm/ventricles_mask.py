import os

import nibabel
import spire

from .. import entrypoint
from ..cli import *

class VentriclesMask(spire.TaskFactory):
    """ Compute a mas of the ventricles using the MEDI toolbox.
    """
    
    def __init__(self, r2_star: str, mask: str, target: str):
        """ :param r2_star: Path to source R2* image (Hz)
            :param mask: Path to binary mask
            :param target: Path to target binary ventricles mask
        """
        
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [r2_star, mask]
        self.targets = [target]
        self.actions = [(__class__.action, (r2_star, mask, target))]

    @staticmethod
    def action(r2_star_path, mask_path, target_path):
        import meg
        
        medi_toolbox_path = os.environ["ERWIN_MEDI"]
        r2_star = nibabel.load(r2_star_path)
        mask = nibabel.load(mask_path)
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            engine["r2_star"] = r2_star.get_fdata()
            engine["mask"] = mask.get_fdata()
            engine["voxel_size"] = r2_star.header["pixdim"][1:1+r2_star.ndim]
            engine("mask = extract_CSF(r2_star, mask, voxel_size);")
            mask = engine["mask"]
        
        nibabel.save(nibabel.Nifti1Image(mask, r2_star.affine), target_path)

def main():
    return entrypoint(VentriclesMask)
