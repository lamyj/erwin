import argparse
import itertools
import sys

import spire

from .. import entrypoint, parsing

class MultiTissueNormalization(spire.TaskFactory):
    """ Multi-tissue informed log-domain intensity normalisation
    
        This wraps mtnormalise from MRtrix3.
    """
    
    def __init__(self, sources, mask, targets):
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
   return entrypoint(
        MultiTissueNormalization, [
            parsing.Multiple(
                ["--sources", {"help": "Source by-tissue images"}]),
            ("--mask", {"help": "mask"}),
            parsing.Multiple(
                ["--targets", {"help": "Target normalized images"}])])
