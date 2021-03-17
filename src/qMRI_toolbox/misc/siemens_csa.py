import base64
import re

def find_csa_group(meta_data):
    csa_group = None
    for key, value in meta_data.items():
        match = re.match(r"(0029)00(\d\d)", key)
        if match:
            creator = b"SIEMENS CSA HEADER"
            is_siemens = (value[0] == creator)
            if not is_siemens:
                try:
                    is_siemens = base64.b64decode(value[0]) == creator
                except:
                    is_siemens = False
            if is_siemens:
                csa_group = (
                    (int(match.group(1), 16) << 16) + 
                    (int(match.group(2), 16) <<  8))
                break
    return csa_group
