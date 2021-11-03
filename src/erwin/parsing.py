import re

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import docutils.utils

def add_arguments(class_, parser):
    """ Add arguments to an ArgumentParser based on the docstring of the class_
        __init__.
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
    
    visitor = Visitor(document)
    document.walk(visitor)
    
    for names, options in visitor.arguments:
        parser.add_argument(*names, **options)

class Visitor(docutils.nodes.NodeVisitor):
    def __init__(self, *args, **kwargs):
        docutils.nodes.NodeVisitor.__init__(self, *args, **kwargs)
        self.arguments = []
    
    def visit_field(self, field):
        field_name, field_body = field.children
        field_type, field_data = field_name.children[0].astext().split(" ", 1)
        
        if field_type != "param":
            return
        
        param_type, param_name = field_data.rsplit(" ", 1)
        
        creator = eval(param_type)
        if not isinstance(creator, Argument):
            creator = Required(param_type)
        
        names = param_name.split(",")
        help = field_body.astext()
        
        self.arguments.append(creator(names, help))
    
    def unknown_visit(self, node):
        pass

class Argument(object):
    def __init__(self, type_, required):
        self.type_ = eval(type_) if isinstance(type_, str) else type_
        self.required = required
    
    def __call__(self, names_or_flags, help):
        options = {"type": self.type_, "required": self.required, "help": help}
        
        return (
            [
                "{}{}".format("-" if len(x) == 1 else "--", x.replace("_", "-"))
                for x in names_or_flags
            ],
            options)

class Required(Argument):
    def __init__(self, type_):
        Argument.__init__(self, type_, True)
    
    def __call__(self, names_or_flags, help):
        return Argument.__call__(self, names_or_flags, help)

class Optional(Argument):
    def __init__(self, type_, default=None):
        Argument.__init__(self, type_, False)
        self.default = default
    
    def __call__(self, names_or_flags, help):
        names, options = Argument.__call__(self, names_or_flags, help)
        options["default"] = self.default
        return names, options

class Sequence(Argument):
    def __init__(self, type_, count=None, optional=False):
        Argument.__init__(self, type_, not optional)
        self.count = int(count) if count is not None else None
    
    def __call__(self, names_or_flags, help):
        name, options = Argument.__call__(self, names_or_flags, help)
        options["nargs"] = self.count if self.count else "+"
        return (name, options)

class Flag(Argument):
    def __init__(self, present, absent, optional=False, prefix=None):
        Argument.__init__(self, type(present), not optional)
        self.present = present
        self.absent = absent
        self.prefix = prefix
    
    def __call__(self, names_or_flags, help):
        name, options = Argument.__call__(self, names_or_flags, help)
        options.update({
            "action": "store_const", "const": self.present,
            "default": self.absent})
        if self.prefix is not None:
            options["dest"] = name[0].split("--", 1)[1]
            name = [
                "--{}-{}".format(self.prefix, x.split("--", 1)[1])
                for x in name if x.startswith("--")]
        
        del options["type"]
        return (name, options)

class Choice(Argument):
    def __init__(self, choices, optional=False):
        Argument.__init__(self, type(choices[0]), not optional)
        self.choices = choices
    
    def __call__(self, names_or_flags, help):
        name, options = Argument.__call__(self, names_or_flags, help)
        options.update({"choices": self.choices})
        return (name, options)
