import spire

from .. import entrypoint
from ..cli import *

class MeanResponse(spire.TaskFactory):
    """ Average ODF response functions.
        
        This wraps responsemean from MRtrix3.
    """
    
    def __init__(self, sources: Tuple[str, ...], target: str):
        """ :param sources: Path to source responses
            :param target: Path to target average response
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = sources
        self.targets = [target]
        
        self.actions = [["responsemean", "-force"] + sources + [target]]

def main():
    return entrypoint(MeanResponse)
