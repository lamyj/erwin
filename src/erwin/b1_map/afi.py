import nibabel
import numpy
import spire

from .. import entrypoint, parsing

class AFI(spire.TaskFactory):
    """ Relative B1 map from an AFI sequence.
        
        Reference: Actual flip-angle imaging in the pulsed steady state: A 
        method for rapid three-dimensional mapping of the transmitted 
        radiofrequency field. Yarnykh. Magnetic Resonance in Medicine 57(1).
        2007.
    """
    
    def __init__(self, source, flip_angle, tr_ratio, target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [source]
        self.targets = [target]
        
        self.actions = [(AFI.b1_map, (source, flip_angle, tr_ratio, target))]
    
    @staticmethod
    def b1_map(source_path, flip_angle, tr_ratio, target_path):
        image = nibabel.load(source_path)
        data = image.get_fdata()
        
        nominal_fa = numpy.radians(flip_angle)
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            r = data[..., 1] / data[..., 0]
        n = tr_ratio
        actual_fa = numpy.arccos((r*n - 1)/(n-r))
        
        nibabel.save(
            nibabel.Nifti1Image(actual_fa/nominal_fa, image.affine), 
            target_path)
        
def main():
    return entrypoint(
        AFI, [
            ("--source", {"help": "Magnitude data of the AFI sequence"}),
            parsing.FlipAngle,
            ("--tr-ratio", {"help": "Ratio between the two TR", "type": float}),
            ("--target", {"help": "Path to the target B1 map"})])
