import spire

from .. import entrypoint

class SphericalDeconvolutionResponse(spire.TaskFactory):
    """ Unsupervised estimation of WM, GM and CSF response functions that does
        not require a T1 image.
        
        This wraps "dwi2response dhollander" from MRtrix3.
    """
    
    def __init__(self, source, prefix, mask=None):
        spire.TaskFactory.__init__(self, prefix+"*.response")
        
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        
        self.targets = [
            "{}{}.response".format(prefix, x) for x in ["wm", "gm", "csf"]]
        
        self.actions = [
            # DWI-based response estimation
            # As of Mrtrix 3.0.0, this is the "improved" Dhollander method.
            ["dwi2response", "dhollander", "-force"]
                + [source] + (["-mask", mask] if mask else []) + self.targets]

def main():
    return entrypoint(
        SphericalDeconvolutionResponse, [
            ("source", {"help": "Source DWI image"}),
            ("prefix", {"help": "Prefix of the target response files"}),
            ("--mask", {"help": "Binary mask"})])
