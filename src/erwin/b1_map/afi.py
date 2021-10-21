import base64
import json
import re

import dicomifier
import nibabel
import numpy
import spire

from .. import entrypoint, misc

class AFI(spire.TaskFactory):
    """ Relative B1 map (factor with respect to the true flip angle) from an
        AFI sequence.
        
        Reference: Actual flip-angle imaging in the pulsed steady state: A 
        method for rapid three-dimensional mapping of the transmitted 
        radiofrequency field. Yarnykh. Magnetic Resonance in Medicine 57(1).
        2007.
    """
    
    def __init__(self, source, target, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        
        self.actions = [(AFI.b1_map, (source, meta_data, target))]
    
    @staticmethod
    def b1_map(source_path, meta_data_path, target_path):
        image = nibabel.load(source_path)
        data = image.get_fdata()
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        nominal_fa = numpy.radians(meta_data["FlipAngle"][0])
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            r = data[..., 1] / data[..., 0]
        n = AFI.get_tr_ratio(meta_data)
        actual_fa = numpy.arccos((r*n - 1)/(n-r))
        
        nibabel.save(
            nibabel.Nifti1Image(actual_fa/nominal_fa, image.affine), 
            target_path)
    
    @staticmethod
    def get_tr_ratio(meta_data):
        """ Read the TR ratio from the private data. """    
        
        protocol = misc.siemens_csa.get_protocol(meta_data)
        if protocol["tSequenceFileName"] != b"%CustomerSeq%\\MAFI":
            raise Exception("Unknown AFI data")
        tr_ratio = protocol["sWiPMemBlock"]["alFree"][5]
        
        return tr_ratio
        
def main():
    return entrypoint(
        AFI, [
            ("source", {"help": "Magnitude data of the AFI sequence"}),
            ("target", {"help": "Path to the target B1 map"}),
            (
                "--meta-data", "-m", {
                    "help": (
                        "Optional meta-data. If not provided, deduced from the "
                        "image.")})])
