import json
import re

import pydicom
import sycomore

from . import siemens
from .. import entrypoint, parsing

units = {
    x:y for x,y in vars(sycomore.units).items()
    if isinstance(y, sycomore.Quantity)}

def get(path, query, unit=None):
    """Return a meta-data item from a file, optionnally scaled by unit."""
    data_set = read_file(path)
    if data_set is None:
        raise Exception("Unknown file type: {}".format(path))

    value = get_meta_data(data_set, query)
    
    if unit is not None:
        value *= parse_unit(unit).magnitude
    
    return value

def read_file(path):
    """Read the file as either DICOM or JSON."""
    with open(path, "rb") as fd:
        try:
            data_set = pydicom.dcmread(fd)
        except pydicom.filereader.InvalidDicomError:
            data_set = None
    
    if not data_set:
        with open(path, "r") as fd:
            try:
                data_set = json.load(fd)
            except Exception:
                data_set = None
    
    return data_set

def get_meta_data(data_set, query):
    value = data_set
    parent_tag = None
    for item in query.split("."):
        contained = False
        try:
            contained = item in value
        except:
            pass
            
        if contained:
            value = value[item]
            parent_tag = item
        elif (
                isinstance(value, list) 
                or isinstance(value, pydicom.DataElement) and value.VR == "SQ"):
            value = value[int(item)]
        else:
            getter_found = False
            for getter in [siemens.get_csa, siemens.get_protocol]:
                try:
                    value = getter(data_set, parent_tag, item, value)
                except:
                    pass
                else:
                    getter_found = True
                
                if getter_found:
                    parent_tag = item
                    break
            
            if not getter_found:
                raise IndexError("No such item: {}".format(query))
    
    if isinstance(value, pydicom.DataElement):
        value = value.value
    
    return value

def parse_unit(unit_string):
    """Parse the string as a sycomore.Quantity."""
    
    operators = r"(\*|\*|/|\(|\))+"
    numbers = "(?:-?\d+)"
    for item in re.split(operators, unit_string):
        is_operand = item in units or re.match(numbers, item)
        is_operator = re.match(operators, item)
        if item and not is_operand and not is_operator:
            raise Exception()

    return eval(unit_string, units)

class Getter(object):
    """Print the value of a meta-data item."""
    
    def __init__(self, path, query, unit=None):
        self.actions = [(Getter.get, (path, query, unit))]
    
    @staticmethod
    def get(path, query, unit):
        value = get(path, query, unit)
        print(value)

def main():
    return entrypoint(
        Getter, [
            ("--path", "-p", {"help": "Input path"}),
            ("--query", "-q", {"help": "Meta-data query"}),
            parsing.Optional(["--unit", "-u", {"help": "Unit of meta-data"}])])
