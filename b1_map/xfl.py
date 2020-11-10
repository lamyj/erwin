import argparse
import base64
import json
import re
import sys

import dicomifier
import nibabel
import spire

class XFL(spire.TaskFactory):
    """ Return the B1 map (as a relative factor of the true flip angle) from an
        XFL sequence. On a single Tx system, the XFL sequence generates four 
        volumes; this class expects the flip angle map as input, usually called
        "B1_Ampli", and expects that the meta-data has been converted by 
        Dicomifier.
        
        Reference: Amadon, et al. B1 Mapping of an 8-Channel TX-Array Over a 
        Human-Head-Like Volume in Less Than 2 Minutes: The XEP Sequence. 
        Proceedings of the 18th Annual ISMRM Meeting (abstract #2828). 2010.
    """
    
    def __init__(self, source, target, meta_data=None):
        spire.TaskFactory.__init__(self, target)
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        
        self.actions = [(XFL.b1_map, (source, meta_data, target))]
    
    def b1_map(source_path, meta_data_path, target_path):
        image = nibabel.load(source_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        fa_prep = XFL.get_fa_prep(meta_data)
        # FA map in XFL is 10*degrees
        fa_map = image.get_fdata()/10.
        nibabel.save(
            nibabel.Nifti1Image(fa_map/fa_prep, image.affine), target_path)
    
    def get_fa_prep(meta_data):
        """ Return the flip angle of the preparation saturation pulse. """
        
        csa_group = None
        for key, value in meta_data.items():
            match = re.match(r"(0029)00(\d\d)", key)
            if match:
                if base64.b64decode(value[0]) == b"SIEMENS CSA HEADER":
                    csa_group = (
                        (int(match.group(1), 16) << 16) + 
                        (int(match.group(2), 16) <<  8))
                    break
        if csa_group is None:
            # Default to the usual location
            csa_group = 0x00291000
        
        series_data_element = "{:08x}".format(csa_group + 0x20)
        csa_data = dicomifier.dicom_to_nifti.siemens.parse_csa(
            base64.b64decode(meta_data[series_data_element][0]))
        protocol = csa_data["MrPhoenixProtocol"][0]
        fa_prep = float(
            re.search(
                    br"sWiPMemBlock.adFree\[0\]\s*=\s*(\S+)$", protocol, re.M
                ).group(1))
        
        return fa_prep

def main():
    parser = argparse.ArgumentParser(description=XFL.__doc__)
    parser.add_argument("source", help="Flip angle map from the XFL")
    parser.add_argument(
        "meta_data", nargs="?", 
        help="Meta-data associated with the source image")
    parser.add_argument("target", help="Path to the target B1 map")
    arguments = parser.parse_args()
    
    task = XFL(**vars(arguments))
    XFL.b1_map(*task.file_dep, *task.targets)

if __name__ == "__main__":
    sys.exit(main())
