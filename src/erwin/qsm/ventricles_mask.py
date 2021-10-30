import nibabel
import spire

from .. import entrypoint

class VentriclesMask(spire.TaskFactory):
    """ Compute a mas of the ventricles using the MEDI toolbox.
    """
    
    def __init__(self, r2_star, mask, target, medi_toolbox):
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [r2_star, mask]
        self.targets = [target]
        self.actions = [(VentriclesMask.mask, (r2_star, mask, medi_toolbox, target))]

    @staticmethod
    def mask(r2_star_path, mask_path, medi_toolbox_path, target_path):
        import meg
        
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
    return entrypoint(
        VentriclesMask, [
            ("--r2-star", {"help": "R2* image"}),
            ("--mask", {"help": "Mask image"}),
            ("--target", {"help": "Ventricles mask"}),
            (
                "--medi", {
                    "dest": "medi_toolbox", 
                    "help": "Path to the MEDI toolbox"})])
