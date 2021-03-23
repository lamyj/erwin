import base64
import json
import re

import dicomifier
import nibabel
import numpy
import spire

from .. import entrypoint, misc

class AFI(spire.TaskFactory):
    """ Return the B1 map (as a relative factor of the true flip angle) from an
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
        
        csa_group = misc.siemens_csa.find_csa_group(meta_data) or 0x00291000
        csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
            base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
        protocol = csa["MrPhoenixProtocol"][0]
        tr_ratio = float(
            re.search(
                    br"sWiPMemBlock.alFree\[5\]\s*=\s*(\S+)$", protocol, re.M
                ).group(1))
        
        return tr_ratio
        
def main():
    return entrypoint(
        AFI, [
            ("source", {"help": "Magnitude data of the AFI sequence"}),
            ("target", {"help": "Path to the target B1 map"})])
