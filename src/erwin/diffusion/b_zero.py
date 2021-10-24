import spire

from .. import entrypoint, parsing

class BZero(spire.TaskFactory):
    """ Extraction and optional average of b=0 s/mm^2 images from DWI data.
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
            ("--source", {"help": "DWI data set"}),
            ("--target", {"help": "Target 4D image of all b=0 volumes"}),
            parsing.Optional([
                "--average", {
                    "action": "store_true",
                    "help": "Average of all b=0 volumes"}])])
