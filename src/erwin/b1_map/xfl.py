import base64
import json
import re

import dicomifier
import nibabel
import spire

from .. import entrypoint, misc

class XFL(spire.TaskFactory):
    """ Relative B1 map (factor with respect to the true flip angle) from an
        XFL sequence.
        
        On a single Tx system, the XFL sequence generates four 
        volumes; this class expects the flip angle map as input, usually called
        "B1_Ampli".
        
        Reference: Amadon, et al. B1 Mapping of an 8-Channel TX-Array Over a 
        Human-Head-Like Volume in Less Than 2 Minutes: The XEP Sequence. 
        Proceedings of the 18th Annual ISMRM Meeting (abstract #2828). 2010.
    """
    
    def __init__(self, source, target, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        
        self.actions = [(XFL.b1_map, (source, meta_data, target))]
    
    @staticmethod
    def b1_map(source_path, meta_data_path, target_path):
        image = nibabel.load(source_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        fa_prep = XFL.get_fa_prep(meta_data)
        # FA map in XFL is 10*degrees
        fa_map = image.get_fdata()/10.
        nibabel.save(
            nibabel.Nifti1Image(fa_map/fa_prep, image.affine), target_path)
    
    @staticmethod
    def get_fa_prep(meta_data):
        """ Return the flip angle of the preparation saturation pulse. """
        
        protocol = misc.siemens_csa.get_protocol(meta_data)
        if protocol["tSequenceFileName"] != b"%CustomerSeq%\\ns_xfl":
            print(protocol["tSequenceFileName"])
            raise Exception("Unknown AFI data")
        fa_prep = protocol["sWiPMemBlock"]["adFree"][0]
        
        return fa_prep

def main():
    return entrypoint(
        XFL, [
            ("source", {"help": "Flip angle map from the XFL"}),
            ("target", {"help": "Path to the target B1 map"}),
            (
                "--meta-data", "-m", {
                    "help": 
                        "Optional meta-data. If not provided, deduced from the "
                        "source image."})])
