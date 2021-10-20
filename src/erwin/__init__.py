import argparse
import logging
import subprocess

def entrypoint(class_, arguments):
    """ Create a main-like function from a task class and a dictionary-based
        description of the command-line arguments. An option to set the 
        verbosity is automatically added.
    """
    
    parser = argparse.ArgumentParser(description=class_.__doc__)
    parser.add_argument(
        "--verbosity", "-v", default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the verbosity level (defaults to \"warning\")")
    
    for entry in arguments:
        if len(entry) == 2:
            name, options = entry
            parser.add_argument(name, **options)
        elif len(entry) == 3:
            long_name, short_name, options = entry
            parser.add_argument(long_name, short_name, **options)
        else:
            raise Exception("Invalid argument specification")
    arguments = vars(parser.parse_args())
    
    logging.getLogger().setLevel(
        getattr(logging, arguments["verbosity"].upper()))
    del arguments["verbosity"]
    
    task = class_(**arguments)
    try:
        for action in task.actions:
            if isinstance(action, list):
                subprocess.check_call(action)
            elif isinstance(action, tuple):
                action[0](*action[1])
    except Exception as e:
        if logging.getLogger().getEffectiveLevel() > logging.DEBUG:
            parser.error(e)
        else:
            raise

from . import (
    b0_map, b1_map, cbf, diffusion, misc, moco, mt_map, qsm, segmentation,
    t1_map, t2_map
)
