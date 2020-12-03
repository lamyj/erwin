import itertools

import spire

from .. import entrypoint

class SphericalHarmonics(spire.TaskFactory):
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
                + list(itertools.chain(*zip(global_response, self.targets))),
            # ["mtnormalise", "-force", "-mask", mask]
            #     +list(itertools.chain(*zip(sh, sh))
        ]

# def main():
#     return entrypoint(
#         Tensor, [
#             ("source", {"help": "Source DWI image"}),
#             ("target", {"help": "Target diffusion tensor image"}),
#             ("--mask", {"help": "Binary mask"}),
#             ("--dkt", {"help": "Target diffusion kurtosis image"}),
#             ("--ols", {"action": "store_true", "help": "Perform initial fit with OLS"}),
#             ("--iter", {"help": "Number of iterative reweightings"}),
#             ("--b0", {"help": "Target estimated b=0 s/mm² image"})])
