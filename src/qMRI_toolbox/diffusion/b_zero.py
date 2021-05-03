import spire

from .. import entrypoint

class BZero(spire.TaskFactory):
    """ Extract the b=0 s/mm^2 images from a DWI data set and optionnaly average
        them.
    """
    
    def __init__(self, source, target, average=False):
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        self.targets = [target]
        
        self.actions = [
            ["dwiextract", "-force", "-quiet", "-bzero", source, target]]
        if average:
            self.actions.append(
                ["mrmath", "-force", "-quiet", target, "mean", "-axis", "3", target])

def main():
    return entrypoint(
        BZero, [
            ("source", {"help": "DWI data set"}),
            ("target", {"help": "Target b=0 image"}),
            ("--average", {
                "action": "store_true", "help": "Apparent fiber density map"})])
