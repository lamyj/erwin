import base64
import re

import dicomifier
import numpy

from .. import misc

def get_pulses(meta_data):
    csa_group = misc.siemens_csa.find_csa_group(meta_data) or 0x00291000
    csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
        base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
    protocol = csa["MrPhoenixProtocol"][0]
    
    pulses = re.findall(
        br"^sTXSPEC.aRFPULSE\[(\d+)\]\.tName\s+=\s+(\S+)$", protocol, 
        re.M)
    
    return pulses

def get_mt_pulse_info(meta_data):
    """ Read the MT pulse informations from the private data. """    
    
    csa_group = misc.siemens_csa.find_csa_group(meta_data) or 0x00291000
    csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
        base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
    protocol = csa["MrPhoenixProtocol"][0]
    
    
    regex_template = r"^sWiPMemBlock.alFree\[{}\]\s*=\s*(\S+)$"
    fields = {4: "angle", 5: "duration", 6: "frequency_offset"}
    
    pulse_info = {
        name: float(
            re.search(
                regex_template.format(i).encode(), protocol, re.M).group(1))
        for i, name in fields.items()}
    
    # Angle in radians
    pulse_info["angle"] = numpy.radians(pulse_info["angle"])
    # Duration in seconds
    pulse_info["duration"] *= 1e-6
    
    return pulse_info
