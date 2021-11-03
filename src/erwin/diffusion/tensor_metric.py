import spire

from .. import entrypoint, parsing

class TensorMetric(spire.TaskFactory):
    """ Maps of tensor-derived parameters
        
        This wraps tensor2metrix from MRtrix3.
    """
    def __init__(self, source, kind, target, num=None, mask=None):
        """ :param str source: Path to source DWI image
            :param Choice(["adc", "fa", "ad", "rd", "value", "vector"]) kind: Metric kind
            :param Optional(int) num: Desired eigenvalue or eigenvector
            :param Optional(str) mask: Path to binary mask image
        """
        
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        self.targets = [target]
        
        self.actions = [
            ["tensor2metric", "-force"] 
                + (["-mask", mask] if mask else [])
                + (["-num", str(num)] if kind in ["value", "vector"] else [])
                + ["-{}".format(kind.lower()), target]
                + [source]]

def main():
    return entrypoint(TensorMetric)
