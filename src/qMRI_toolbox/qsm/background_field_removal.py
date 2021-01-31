import json
import re

import meg
import nibabel
import numpy
import spire

from .. import entrypoint

class BackgroundFieldRemoval(spire.TaskFactory):
    """ Remove the background field
    """
    
    def __init__(self, f_total, mask, target, medi_toolbox, ):
        spire.TaskFactory.__init__(self, target)
        
        self.file_dep = [f_total, mask]
        self.targets = [target]
        
        self.actions = [
            (BackgroundFieldRemoval.lbv, (f_total, mask, medi_toolbox, target))]
    
    def lbv(f_total_path, mask_path, medi_toolbox_path, target_path):
        f_total_image = nibabel.load(f_total_path)
        mask_image = nibabel.load(mask_path)
        
        with meg.Engine() as engine:
            engine(f"run('{medi_toolbox_path}/MEDI_set_path.m');")
            
            engine["f_total"] = f_total_image.get_fdata()
            engine["mask"] = numpy.array(mask_image.dataobj)
            engine["shape"] = numpy.array(f_total_image.shape[:3], float)
            engine["voxel_size"] = f_total_image.header["pixdim"][1:4]
            
            engine("f_object = LBV(f_total, mask, shape, voxel_size, 0.005);")
            f_object = engine["f_object"]
        
        nibabel.save(
            nibabel.Nifti1Image(f_object, f_total_image.affine), target_path)

def main():
    return entrypoint(
        BackgroundFieldRemoval, [
            ("f_total", {"help": "Total field image"}),
            ("mask", {"help": "Mask image"}),
            ("target", {"help": "Object field image"}),
            (
                "--medi", {
                    "required": True, 
                    "dest": "medi_toolbox", 
                    "help": "Path to the MEDI toolbox"})])
