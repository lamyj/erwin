import spire

from .. import entrypoint

class Mask(spire.TaskFactory):
    """ Whole brain mask from a DWI image
        
        This wraps dwi2mask from MRtrix3.
    """ 
    def __init__(self, source, target):
        """ :param str source: Path to DWI data
            :param str target: Path to the target mask
        """
        
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [["dwi2mask", "-force", source, target]]

def main():
    return entrypoint(Mask)
