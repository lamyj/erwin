import spire

from .. import entrypoint, parsing

class Tensor(spire.TaskFactory):
    """ Diffusion and optional kurtosis tensor estimation.
        
        This wraps dwi2tensor from MRtrix3.
    """
    
    def __init__(
            self, source, target, 
            mask=None, dkt=None, ols=False, iter=None, b0=None):
        """ :param str source: Path to source diffusion-weighted image
            :param str target: Path to target diffusion tensor image
            :param Optional(str) mask: Path to binary mask
            :param Optional(str) dkt: Path to target diffusion kurtosis image
            :param Flag(True, False, True) ols: Perform initial fit with OLS
            :param Optional(int) iter: Number of iterative reweightings
            :param Optional(str) b0: Path to target estimated b=0 s/mm² image
        """
        
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
    return entrypoint(Tensor)
