import itertools

import spire

from .. import entrypoint

class SphericalHarmonics(spire.TaskFactory):
    """ Perform multi-shell multi-tissue CSD.
        
        This wraps dwi2fod msmt_csd from MRtrix3.
    """
    
    def __init__(
            self, source, global_response, prefix, 
            mask=None):
        spire.TaskFactory.__init__(self, prefix+"*.mif.gz")
        
        self.file_dep = [source]+global_response
        if mask is not None:
            self.file_dep.append(mask)
        
        self.targets = [
            "{}{}.mif.gz".format(prefix, x) for x in ["wm", "gm", "csf"]]
        
        self.actions = [
            ["dwi2fod", "-force", "msmt_csd", source]
                + (["-mask", mask] if mask else [])
                + list(itertools.chain(*zip(global_response, self.targets)))
        ]

def main():
    return entrypoint(
        SphericalHarmonics, [
            ("--source", {"help": "Source DWI image"}),
            ("--global-response", {"help": "Single-fiber response files"}),
            ("--prefix", {"help": "Prefix of the target harmonics files"})])
