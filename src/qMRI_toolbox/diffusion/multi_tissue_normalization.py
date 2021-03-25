import argparse
import itertools
import sys

import spire

from .. import entrypoint

class MultiTissueNormalization(spire.TaskFactory):
    """ Multi-tissue informed log-domain intensity normalisation (mtnormalise
        from MRtrix3)
    """
    
    def __init__(self, sources, mask, targets):
        spire.TaskFactory.__init__(self, str(targets[0]))
        self.file_dep = sources
        self.targets = targets
        self.actions = [
            ["mtnormalise", "-force", "-mask", mask]
                +list(itertools.chain(*zip(sources, targets)))
        ]

def main():
    # WARNING: this is a very hackish way to ensure that the number of sources
    # and targets are the same.
    class SameNumberOfArguments(argparse.Action):
        def __init__(self, option_strings, dest, nargs=None, **kwargs):
            if nargs is not None:
                raise ValueError("nargs not allowed")
            
            nargs = (len(sys.argv)-2)//2
            argparse.Action.__init__(self, option_strings, dest, nargs, **kwargs)
        
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
    
    return entrypoint(
        MultiTissueNormalization, [
            (
                "sources", {
                    "metavar": "source", "action": SameNumberOfArguments,
                    "help": "Source by-tissue images"}),
            ("mask", {"help": "mask"}),
            (
                "targets", {
                    "metavar": "target", "action": SameNumberOfArguments,
                    "help": "Target normalized images"})])
