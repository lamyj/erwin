import argparse
import logging
import os
import re
import subprocess

import nibabel
import numpy

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
        
        action = parser.add_argument(*names, **options)
        nargs = action.nargs if action.nargs is not None or action.choices else 1
        if nargs == 1:
            action.metavar = names[0].lstrip("-")[0].upper()
        elif isinstance(nargs, int) and nargs > 1:
            action.metavar = tuple(
                "{}{}".format(names[0].lstrip("-")[0].upper(), x)
                for x in range(1, nargs+1))
        elif nargs == "+":
            action.metavar = tuple(
                "{}{}".format(names[0].lstrip("-")[0].upper(), x)
                for x in range(1, 3))
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

def parse_slice(string):
    match = re.match("^\[(.+)\]$", string)
    if match:
        items = re.split(",", match.group(1))
    else:
        items = []

    for index, item in enumerate(items):
        if item == "...":
            items[index] = Ellipsis
        else:
            elements = item.split(":")
            if not elements:
                items[index] = None
            elif len(elements) == 1:
                items[index] = int(elements[0])
            else:
                items[index] = slice(*[
                    int(x) if x else None for x in item.split(":")])

    return tuple(items)

def load(string):
    if os.path.isfile(string):
        return nibabel.load(string)
    else:
        # NOTE: may be a pathlib.Path
        match = re.match(r"^(.+)(\[.+\])$", str(string))
        if not match:
            raise FileNotFoundError(f"No such file or no access: '{string}'")
        path, slice_string = match.groups()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"No such file or no access: '{path}'")
        image = nibabel.load(path)
        slice_ = parse_slice(slice_string)
        if not slice_:
            raise ValueError(f"Invalid slice: '{slice_string}'")

        subset = nibabel.Nifti1Image(
            numpy.array(image.dataobj)[slice_], image.affine)

        return subset

def get_path(string):
    # NOTE: may be a pathlib.Path
    match = re.match(r"^(.+)(\[.+\])$", str(string))
    if not match:
        return string
    else:
        return match.group(1)

from . import (
    cli, b0_map, b1_map, cbf, diffusion, meta_data, misc, moco, mt_map, qsm,
    segmentation, t1_map, t2_map
)
