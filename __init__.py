import argparse
import subprocess

def entrypoint(class_, arguments):
    parser = argparse.ArgumentParser(description=class_.__doc__)
    for name, options in arguments:
        parser.add_argument(name, **options)
    arguments = parser.parse_args()
    
    task = class_(**vars(arguments))
    for action in task.actions:
        if isinstance(action, list):
            subprocess.check_call(action)
        elif isinstance(action, tuple):
            action[0](*action[1])

from . import b0_map, b1_map, diffusion, mt_map, t1_map, t2_map
