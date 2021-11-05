import spire

from .. import entrypoint
from ..cli import *

class BZero(spire.TaskFactory):
    """ Extraction and optional average of b=0 s/mm^2 images from DWI data.
    """
    
    def __init__(self, source: str, target: str, average: Flag=False):
        """ :param source: Path to DWI data
            :param target: Path to target 4D image of all b=0 volumes
            :param average: Compute average of all b=0 volumes
        """
        print(source, target, average)
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        self.targets = [target]
        
        self.actions = [
            ["dwiextract", "-force", "-quiet", "-bzero", source, target]]
        if average:
            self.actions.append(
                ["mrmath", "-force", "-quiet", target, "mean", "-axis", "3", target])

def main():
    return entrypoint(BZero)
