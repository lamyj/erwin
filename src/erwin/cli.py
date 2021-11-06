import inspect
import re
import typing

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import sphinx.util.typing

class Choice(object):
    """ Type hint corresponding to an enumeration
    """
    def __init__(self, args):
        self.__origin__ = Choice
        self.__args__ = args
    
    def __call__(self, *args, **kwargs):
        """ This function is required by Python 3.9
        """
        pass
    
    def __class_getitem__(cls, key):
        return cls(key)
    
    @classmethod
    def __str__(self):
        return "foo"

class Flag(object): 
    """ Type hint, equivalent to a boolean, corresponding to a command-line flag
    """
    pass

original_stringify = sphinx.util.typing.stringify
def stringify(annotation: typing.Any) -> str:
    if isinstance(annotation, Choice):
        return "{}[{}]".format(
            annotation.__class__.__name__,
            ", ".join(repr(x) for x in annotation.__args__))
    elif annotation == Flag:
        return original_stringify(typing.Optional[bool])
    else:
        return original_stringify(annotation)
sphinx.util.typing.stringify = stringify

def get_arguments(class_):
    """ Using the class docstring, and the type hints and docstring of the class
        __init__, return a list of (name, options) to pass to 
        ArgumentParser.add_argument
    """
    arguments = []
    
    annotations = typing.get_type_hints(class_.__init__)
    defaults = {
        k: v.default
        for k,v in inspect.signature(class_.__init__).parameters.items()}
    param_fields = get_param_fields(class_)
    for name in annotations:
        annotation = annotations[name]
        default = defaults[name]
        help = param_fields[name]
        if hasattr(annotation, "__origin__"):
            type_, args = annotation.__origin__, annotation.__args__
        else:
            type_, args = annotation, None
        
        arguments.append(get_argument(name, type_, args, default, help))
    
    return arguments

def get_argument(name, type_, args, default, help):
    """ Return a pair of (name, options) to pass to ArgumentParser.add_argument
        
        :param name: name of the argument
        :param type_: type hint, either a basic type or a parameterized type
        :param args: arguments to a parameterized type
        :param default: default value of the argument, ignore if equal to
            inspect.Parameter.empty
        :param help: Help string
    """
    
    argument = None
    if type_ is Flag:
        argument = get_argument(name, bool, None, default, help)
        del argument[1]["type"]
        argument[1]["required"] = False
        argument[1]["action"] = "store_true" if not default else "store_false"
    elif args is None:
        argument = [
            "--{}".format(name.replace("_", "-")),
            {"type": type_, "required": True, "help": help}]
    elif type_ is typing.Union and len(args) == 2 and args[1] is type(None):
        annotation = args[0]
        if hasattr(annotation, "__origin__"):
            type_, args = annotation.__origin__, annotation.__args__
        else:
            type_, args = annotation, None
        argument = get_argument(name, type_, args, inspect.Parameter.empty, help)
        argument[1]["required"] = False
        if default is not inspect.Parameter.empty:
            argument[1]["default"] = default
    elif type_ is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            argument_type = args[0]
            nargs = "+"
        else:
            if not all([x is args[0] for x in args]):
                raise Exception("Heterogeneous tuple")
            argument_type = args[0]
            nargs = len(args)
        argument = get_argument(
            name, argument_type, None, inspect.Parameter.empty, help)
        argument[1]["nargs"] = nargs
    elif type_ is Choice:
        argument = get_argument(
            name, type(args[0]), None, inspect.Parameter.empty, help)
        argument[1]["choices"] = args
    
    return argument

def get_param_fields(class_):
    """ Return the `param` fields of a RST document.
    """
    
    settings = docutils.frontend.OptionParser(
            components=(docutils.parsers.rst.Parser,)
        ).get_default_values()
    document = docutils.utils.new_document(None, settings)
    rst_parser = docutils.parsers.rst.Parser()
    
    # Normalize the spaces at the start of lines to avoid misleading the parser
    docstring = re.sub(
        r"^\s+", r" ", class_.__init__.__doc__, flags=re.MULTILINE)
    rst_parser.parse(docstring, document)
    
    visitor = GetParamFields(document)
    document.walk(visitor)
    
    return visitor.fields

class GetParamFields(docutils.nodes.NodeVisitor):
    """ Return the `param` fields of a RST document.
    """
    def __init__(self, *args, **kwargs):
        docutils.nodes.NodeVisitor.__init__(self, *args, **kwargs)
        self.fields = {}
    
    def visit_field(self, field):
        field_name, field_body = field.children
        field_type, field_data = field_name.children[0].astext().split(" ", 1)
        
        if field_type != "param":
            return
        
        self.fields[field_data] = field_body.astext()
    
    def unknown_visit(self, node):
        pass

# Easy access to main type hints
from typing import Optional, Tuple
