import argparse

import spire

from .. import execute

class Mask(spire.TaskFactory):
    def __init__(self, source, target):
        self.file_dep = [source]
        self.targets = [target]
        self.actions = [["dwi2mask", "-force", source, target]]

def main():
    parser = argparse.ArgumentParser(description=Mask.__doc__)
    parser.add_argument("source", help="Diffusion-weighted image")
    parser.add_argument("target", help="Path to the target mask")
    arguments = parser.parse_args()
    
    task = Mask(**vars(arguments))
    for action in task.actions:
        execute(action)
