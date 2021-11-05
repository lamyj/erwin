import argparse
import logging
import subprocess

def run(tasks):
    """ Run the given Spire tasks in order.
    """
    
    for task in tasks:
        for action in task.actions:
            if isinstance(action, list):
                subprocess.check_call(action)
            elif isinstance(action, tuple):
                action[0](*action[1])

def entrypoint(class_, aliases=None):
    """ Create a main-like function from a task class and a dictionary-based
        description of the command-line arguments. An option to set the 
        verbosity is automatically added.
    """
    
    aliases = aliases or {}
    parser = argparse.ArgumentParser(description=class_.__doc__)
    parser.add_argument(
        "--verbosity", "-v", default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the verbosity level (defaults to \"warning\")")
    for name, options in cli.get_arguments(class_):
        names = [name]
        name_aliases = aliases.get(name.split("--", 1)[1].replace("-", "_"))
        if name_aliases:
            if isinstance(name_aliases, str):
                name_aliases = [name_aliases]
            for alias in name_aliases:
                if len(alias) == 1:
                    names.append("-{}".format(alias))
                else:
                    names.append("--{}".format(alias.replace("_", "-")))
        parser.add_argument(*names, **options)
    arguments = vars(parser.parse_args())
    
    logging.getLogger().setLevel(
        getattr(logging, arguments["verbosity"].upper()))
    del arguments["verbosity"]
    
    try:
        task = class_(**arguments)
        run([task])
    except Exception as e:
        if logging.getLogger().getEffectiveLevel() > logging.DEBUG:
            parser.error(e)
        else:
            raise

from . import (
    cli, b0_map, b1_map, cbf, diffusion, meta_data, misc, moco, mt_map, qsm,
    segmentation, t1_map, t2_map
)
