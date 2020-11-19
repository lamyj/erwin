import spire

from .. import entrypoint

class Tensor(spire.TaskFactory):
    def __init__(self, source, target, mask=None):
        spire.TaskFactory.__init__(self, target)
        self.file_dep = [source]
        if mask is not None:
            self.file_dep.append(mask)
        self.targets = [target]
        self.actions = [
            ["dwi2tensor", "-force"] 
                + (["-mask", mask] if mask else [])
                + [source, target]]

def main():
    return entrypoint(
        Tensor, [
            ("source", {"help": "Source DWI image"}),
            ("target", {"help": "Target diffusion tensor image"}),
            ("--mask", {"help": "Binary mask"})])
