import base64
import re

import dicomifier

def find_private_group(meta_data, private_creator, group):
    private_group = None
    for element in range(0, 256):
        item = "{:04x}00{:02x}".format(group, element)
        if item in meta_data and meta_data[item][0] == private_creator:
            private_group = (group << 16) + (element << 8)
            break
    return private_group

def find_csa_group(meta_data):
    return find_private_group(meta_data, "SIEMENS CSA HEADER", 0x0029)

def get_protocol(meta_data):
    csa_group = find_csa_group(meta_data) or 0x00291000
    if not csa_group:
        raise Exception("Private group not found")
    csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
        base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
    
    match = re.search(
        br"### ASCCONV BEGIN ###\s*(.*)\s*### ASCCONV END ###", 
        csa["MrPhoenixProtocol"][0], flags=re.DOTALL|re.MULTILINE)
    if not match:
        raise Exception("No protocol found")
    
    protocol = dicomifier.dicom_to_nifti.siemens.parse_protocol(match.group(1).strip())
    return protocol
