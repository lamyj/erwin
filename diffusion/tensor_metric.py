import spire

from .. import entrypoint

class TensorMetric(spire.TaskFactory):
    def __init__(self, source, kind, target, mask=None):
        spire.TaskFactory.__init__(self, target)
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        self.targets = [target]
        
        self.actions = [
            ["tensor2metric", "-force"] 
                + (["-mask", mask] if mask else [])
                + ["-{}".format(kind.lower()), target]
                + [source]]

def main():
    return entrypoint(
        TensorMetric, [
            ("source", {"help": "Source DWI image"}),
            ("kind", {"choices": ["adc", "fa", "ad", "rd"], "help": "Metric kind"}),
            ("target", {"help": "Target diffusion tensor image"}),
            ("--mask", {"help": "Binary mask"})
        ])
