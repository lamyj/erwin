import spire

from .. import entrypoint
from ..cli import *

class Mask(spire.TaskFactory):
    """ Whole brain mask from a DWI image
        
        This wraps dwi2mask from MRtrix3.
    """ 
    def __init__(self, source: str, target: str):
        """ :param source: Path to DWI data
            :param target: Path to the target mask
        """
        
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [["dwi2mask", "-force", source, target]]

def main():
    return entrypoint(Mask)
