import nibabel
import pathlib
import shutil
import subprocess
import tempfile

import spire

from .. import entrypoint
from ..cli import *

class BET(spire.TaskFactory):
    """ Brain extration using BET from FSL.
    """
    
    def __init__(
            self, source: str, target: str, 
            mask: Optional[str]=None, skull: Optional[str]=None,
            no_brain: Flag=False,
            fractional_intensity_threshold: Optional[float]=None,
            vertical_gradient: Optional[float]=None, 
            radius: Optional[float]=None,
            center_of_gravity: Optional[Tuple[int,int,int]]=None,
            thresholding: Flag=False, brain_mesh: Optional[str]=None,
            variant: Optional[Choice[
                "robust", "optic", "neck", "small_fov", "fmri",
                "additionnal_surfaces"]]=None):
        """ :param source: Path to source image
            :param target: Path to target brain image
            :param mask: Path to target brain mask
            :param skull: Path to target skull mask
            :param no_brain: Whether to store the brain image
            :param fractional_intensity_threshold: Fractional intensity threshold
            :param vertical_gradient: Vertical gradient
            :param radius: Initial radius (mm)
            :param center_of_gravity: Center of gravity (voxels)
            :param thresholding: Apply thresholding to segmented brain image and mask
            :param brain_mesh: Path to target brain mesh
            :param variant: Variations on default bet2 functionality
        """
        
        brain = not no_brain
        
        self.targets = []
        if brain:
            self.targets.append(target)
        if mask is not None:
            self.targets.append(mask)
        if skull is not None:
            self.targets.append(skull)
        
        spire.TaskFactory.__init__(self, str(self.targets[0]))
        
        self.file_dep = [source]
        
        self.actions = [
            (
                BET.bet, (
                    source, target, mask, skull, brain,
                    fractional_intensity_threshold, vertical_gradient, radius,
                    center_of_gravity, thresholding, brain_mesh, variant))
        ]
    
    @staticmethod
    def bet(
            source, target, 
            mask=None, skull=None, brain=True,
            fractional_intensity_threshold=None, vertical_gradient=None, 
            radius=None, center_of_gravity=None, thresholding=False, 
            brain_mesh=None, variant=None):
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = pathlib.Path(temp_dir)
            
            command = ["bet", str(temp_dir/"source.nii"), str(temp_dir/"bet")]
            
            if mask is not None:
                command += ["-m"]
            if skull is not None:
                command += ["-s"]
            if not brain:
                command += ["-n"]
            
            if fractional_intensity_threshold is not None:
                command += ["-f", str(fractional_intensity_threshold)]
            if vertical_gradient is not None:
                command += ["-g", str(vertical_gradient)]
            
            if radius is not None:
                command += ["-r", str(radius)]
            
            if center_of_gravity is not None:
                command += ["-c"]+[str(x) for x in center_of_gravity]
            
            if thresholding:
                command += ["-t"]
            
            if brain_mesh is not None:
                command += ["-e"]
            
            if variant == "robust":
                command += ["-R"]
            elif variant == "optic":
                command += ["-S"]
            elif variant == "neck":
                command += ["-B"]
            elif variant == "small_fov":
                command += ["-Z"]
            elif variant == "fmri":
                command += ["-F"]
            elif variant == "additional_surfaces":
                command += ["-F"]
            
            # BET can't handle paths with spaces
            nibabel.save(nibabel.load(source), temp_dir/"source.nii")
            
            subprocess.check_call(command)
            
            if brain:
                nibabel.save(
                    nibabel.load(str(next(iter(temp_dir.glob("bet.*"))))), 
                    target)
            if mask is not None:
                nibabel.save(
                    nibabel.load(str(next(iter(temp_dir.glob("bet_mask.*"))))), 
                    mask)
            if skull is not None:
                nibabel.save(
                    nibabel.load(str(next(iter(temp_dir.glob("bet_skull.*"))))),
                    skull)
            if brain_mesh is not None:
                shutil.copy(temp_dir/"bet_mesh.vtk", brain_mesh)

def main():
    return entrypoint(
        BET, {
            "fractional_intensity_threshold": "f", "vertical_gradient": "g",
            "center_of_gravity": "cog"})
