import importlib
import inspect
import re
import os
import sys
import textwrap
import unittest.mock

def main():
    return_code = 0
    
    if not sys.argv[1:] or sys.argv[1] in ["--help", "-h"]:
        help()
    elif sys.argv[1] in ["--list", "-l"]:
        list()
    else:
        return_code = run(sys.argv[1], sys.argv[1:])
    
    return return_code

def help():
    """ Show the top-level package help.
    """
    
    usage = textwrap.dedent("""\
        usage: {} [-h|-l]
        
        optional arguments:
          -h, --help            show this help message and exit
          -l, --list            show list of known modules"""
        ).format(os.path.basename(sys.argv[0]))
    print(usage)

def list():
    """ Show the list of submodules.
    """
    
    package = sys.modules[__name__].__package__
    stack = [sys.modules[package]]
    scanned = set()
    
    modules = []
    while stack:
        module = stack.pop()
        scanned.add(id(module))
        for name, value in module.__dict__.items():
            if not inspect.ismodule(value) or not value.__package__.startswith(package):
                continue
            if id(value) in scanned:
                continue
            stack.append(value)
            scanned.add(id(value))
            if "main" not in dir(value):
                continue
            
            full_name = "{}.{}".format(value.__package__, name)
            # NOTE: the "entrypoint" function is a relative import in the 
            # modules, and must then be patched at the individual module level,
            # not at its original definition.
            with unittest.mock.patch("{}.entrypoint".format(full_name), get_doc):
                doc = getattr(value, "main")()
                modules.append([full_name[1+len(package):], doc])
    
    max_name_length = max([len(x[0]) for x in modules])
    doc_width = min(110, os.get_terminal_size()[0]) - max_name_length - 1
    
    modules.sort(key=lambda x: x[0])
    for name, doc in modules:
        doc_lines = textwrap.wrap(doc, doc_width)
        print(
            "{}{}{}".format(
                name, (max_name_length-len(name)+1)*" ", doc_lines[0]))
        for doc_line in doc_lines[1:]:
            print("{}{}".format((max_name_length+1)*" ", doc_line))
        print()

def run(module_name, arguments):
    """ Run the specified module with its arguments.
    """
    
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    module_name = module_name.strip(".")
    
    return_code = 0
    try:
        module = importlib.import_module(
            "{}.{}".format(sys.modules[__name__].__package__, module_name))
    except ModuleNotFoundError as e:
        print("No such module: {}\n".format(e))
        help()
        return_code = 1
    else:
        sys.argv = arguments
        return_code = module.main()
    
    return return_code

def get_doc(class_, _):
    """ Return the first paragraph of the specified class docstring.
    """
    
    paragraph = re.split("^\s*$", class_.__doc__.strip(), flags=re.MULTILINE)[0]
    paragraph = re.sub("\s+", " ", paragraph)
    return paragraph

if __name__ == "__main__":
    sys.exit(main())
