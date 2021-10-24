import spire

from .. import entrypoint

class MeanResponse(spire.TaskFactory):
    """ Average ODF response functions.
        
        This wraps responsemean from MRtrix3.
    """
    
    def __init__(self, sources, target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = sources
        self.targets = [target]
        
        self.actions = [["responsemean", "-force"] + sources + [target]]

def main():
    return entrypoint(
        MeanResponse, [
            ("--sources", {"nargs": "+", "help": "Source responses"}),
            ("--target", {"help": "Target average response"})
        ])
