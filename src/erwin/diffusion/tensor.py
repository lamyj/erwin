import spire

from .. import entrypoint, parsing

class Tensor(spire.TaskFactory):
    """ Diffusion and optional kurtosis tensor estimation.
        
        This wraps dwi2tensor from MRtrix3.
    """
    
    def __init__(
            self, source, target, 
            mask=None, dkt=None, ols=False, iter=None, b0=None):
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        self.targets = [target]
        self.actions = [
            ["dwi2tensor", "-force"] 
                + (["-mask", mask] if mask else [])
                + (["-dkt", dkt] if dkt else [])
                + (["-ols"] if ols else [])
                + (["-iter", str(iter)] if iter else [])
                + (["-b0", b0] if b0 else [])
                + [source, target]]

def main():
    return entrypoint(
        Tensor, [
            ("--source", {"help": "Source DWI image"}),
            ("--target", {"help": "Target diffusion tensor image"}),
            parsing.Optional(["--mask", {"help": "Binary mask"}]),
            parsing.Optional(
                ["--dkt", {"help": "Target diffusion kurtosis image"}]),
            parsing.Optional(
                [
                    "--ols", {
                        "action": "store_true",
                        "help": "Perform initial fit with OLS"}]),
            parsing.Optional(
                ["--iter", {"help": "Number of iterative reweightings"}]),
            parsing.Optional(
                ["--b0", {"help": "Target estimated b=0 s/mm² image"}])])
