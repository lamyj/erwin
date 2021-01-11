import argparse

import spire

from .. import entrypoint

class Mask(spire.TaskFactory):
    def __init__(self, source, target):
        spire.TaskFactory.__init__(self, str(target))
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [["dwi2mask", "-force", source, target]]

def main():
    return entrypoint(
        Mask, [
            ("source", {"help": "Diffusion-weighted image"}),
            ("target", {"help": "Path to the target mask"})])
