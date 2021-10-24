import base64
import json
import re

import dicomifier

from .. import entrypoint

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

class ProtocolItem(object):
    """ Return a parameter value from the MR protocol.
    """
    
    def __init__(self, meta_data, path):
        with open(meta_data) as fd:
            meta_data = json.load(fd)
        protocol = get_protocol(meta_data)
        
        self.actions = [(ProtocolItem.get_value, (protocol, path))]
    
    @staticmethod
    def get_value(protocol, path):
        value = protocol
        for item in path.split("."):
            match = re.match(r"^(\w+)\[(\d+)\]$", item)
            
            if match:
                name, index = match.groups()
                index = int(index)
            else:
                name = item
                index = None
            try:
                value = value[name]
                if index is not None:
                    value = value[index]
            except:
                raise Exception("No such item: {}".format(item))
        if isinstance(value, bytes):
            value = value.decode()
        print(value)

def main():
    return entrypoint(
        ProtocolItem, [
            ("--meta-data", {"help": "Siemens meta-data"}),
            (
                "--path", {
                    "help": 
                        "Path to the element inside the protocol "
                        "e.g. sTXSPEC.asNucleusInfo[0].tNucleus"})]
    )
