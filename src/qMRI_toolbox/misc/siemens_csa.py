import base64
import re

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
    
