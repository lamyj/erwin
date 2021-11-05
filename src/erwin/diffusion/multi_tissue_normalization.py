import itertools
import sys

import spire

from .. import entrypoint
from ..cli import *

class MultiTissueNormalization(spire.TaskFactory):
    """ Multi-tissue informed log-domain intensity normalisation
    
        This wraps mtnormalise from MRtrix3.
    """
    
    def __init__(
            self, sources: Tuple[str, ...], mask: str, targets: Tuple[str, ...]):
        """ :param sources: Path to source by-tissue images
            :param mask: Path to mask image
            :param targets: Path to target normalized images
        """
        
        spire.TaskFactory.__init__(self, str(targets[0]))
        self.file_dep = sources
        self.targets = targets
        self.actions = [
            [
                "mtnormalise", "-force", "-mask", mask,
                *itertools.chain(*zip(sources, targets))
            ]
        ]

def main():
   return entrypoint(MultiTissueNormalization)
