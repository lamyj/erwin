import base64
import re
import dicomifier

def get_pulses(meta_data):
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
    
    csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
        base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
    protocol = csa["MrPhoenixProtocol"][0]
    
    pulses = re.findall(
        br"^sTXSPEC.aRFPULSE\[(\d+)\]\.tName\s+=\s+(\S+)$", protocol, 
        re.M)
    
    return pulses
