#!/usr/bin/env python3

import base64
import os
import re
import sys

import dicomifier

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_pulse_info(meta_data, info):
    """ Read the MT pulse informations from the private data. """    
    
    protocol = dicomifier.dicom_to_nifti.siemens.parse_csa(
            base64.b64decode(meta_data["00291020"][0]))["MrPhoenixProtocol"][0]

    if info == "FA":
        pulse_info = float(re.search(br"sWiPMemBlock.alFree\[4\]\s*=\s*(\S+)$", protocol, re.M).group(1))
    elif info == "length":
        pulse_info = float(re.search(br"sWiPMemBlock.alFree\[5\]\s*=\s*(\S+)$", protocol, re.M).group(1))
    elif info == "offset":
        pulse_info = float(re.search(br"sWiPMemBlock.alFree\[6\]\s*=\s*(\S+)$", protocol, re.M).group(1))
    
    return pulse_info