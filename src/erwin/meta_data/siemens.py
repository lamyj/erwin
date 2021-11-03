import base64
import re
import struct

import pydicom

def get_csa(data_set, parent_tag, item, value):
    """ Search for content in a CSA element of a Siemens data set.
    """
    
    # NOTE: the private creator may be stored in a binary VR and thus be
    # base64-encoded
    csa_header = "SIEMENS CSA HEADER"
    csa_headers = [
        csa_header, base64.b64encode(csa_header.encode()).decode()]
    
    match = re.match(r"0029(\d\d)\d\d", parent_tag)
    if match:
        private_creator = data_set["002900{}".format(match.group(1))]
        if isinstance(private_creator, pydicom.DataElement):
            private_creator = private_creator.value
        if isinstance(private_creator, list):
            private_creator = private_creator[0]
        if private_creator not in csa_headers:
            raise Exception("Not a Siemens data set")
        
        try:
            csa = parse_csa(value)
        except Exception as e:
            csa = parse_csa(base64.b64decode(value))
        
        return csa[item]
    else:
        raise Exception("Not in correct tag range")

def get_protocol(data_set, parent_tag, item, value):
    """ Search for content in an MrPhoenixProtocol element of a Siemens data set.
    """
    
    if parent_tag != "MrPhoenixProtocol":
        raise Exception("Not in MrPhoenixProtocol")
    
    match = re.search(
        br"### ASCCONV BEGIN ###\s*(.*?)\s*### ASCCONV END ###", 
        value, flags=re.DOTALL|re.MULTILINE)
    if not match:
        raise Exception("No protocol found")
    
    protocol = parse_protocol(match.group(1))
    return protocol[item]

def parse_csa(csa):
    """ Return a dictionary of (tag, items) of the CSA.
    """

    format = ("<"  # Little-endian
              "4s" # SV10
              "4s" # \x04\x03\x02\x01
              "I"  # Number of items
              "I"  # Unknown
        )
    size = struct.calcsize(format)

    version, _, number_of_elements, _ = struct.unpack(format, csa[:size])

    start = size
    content = {}
    for _ in range(number_of_elements) :
        (name, items), size = parse_element(csa, start)
        content[name] = items
        start += size

    return content

def parse_element(csa, start):
    """ Return a pair (name, items), total_size
    """
    format = ("<"   # Little endian
              "64s" # Name
              "I"   # VM
              "2s"  # VR
              "2s"  # Unknown (end of VR ?)
              "I"   # Syngo datatype
              "I"   # Number of items
              "I"   # Unknown
        )
    size = struct.calcsize(format)

    name, vm, vr, _, syngo_datatype, number_of_items, _ = struct.unpack(
        format, csa[start:start+size])
    name = name.split(b"\x00")[0].decode()

    total_size = size
    start += size
    items = []
    for i in range(number_of_items) :
        item, size = parse_item(csa, start)
        if i < vm :
            if vr in [b"DS", b"FL", b"FD"] :
                item = float(item[:-1])
            elif vr in [b"IS", b"SS", b"US", b"SL", b"UL"] :
                item = int(item[:-1])
            items.append(item)
        start += size
        total_size += size

    return (name, items), total_size

def parse_item(csa, start):
    """ Return a pair content, size
    """
    format = ("<"  # Little endian
              "4I" # Length
             )
    header_size = struct.calcsize(format)

    length = struct.unpack(format, csa[start:start+header_size])

    format = ("<"    # Little endian
              "{0}s" # Content
              "{1}s" # Padding (?)
             ).format(length[1], (4-length[1]%4)%4)
    content_size = struct.calcsize(format)
    content, padding = struct.unpack(
        format, csa[start+header_size:start+header_size+content_size])

    return content, header_size+content_size

def parse_protocol(data):
    """ Parse (as a nested dictionary) the ASCII version of protocol data.
    """

    integer_types = [
        "c", "i", "l", "n", "s",
        "uc", "ui", "ul", "un", "us",
    ]
    floating_point_types = ["fl", "d"]
    types = integer_types+floating_point_types+["s", "b", "t"]

    def integer_parser(value):
        return int(value, 16 if value.startswith(b"0x") else 10)

    def floating_point_parser(value):
        return float(value)

    def string_parser(value):
        # Remove beginning and ending quotes
        if all(c==b'"' for c in value):
            return b""
        else:
            return re.match(br"\"*(.*[^\"])\"*", value).group(1)

    def value_parser(type_, value):
        if type_ == b"b":
            value = bool(integer_parser(value))
        elif type_ == b"t":
            value = string_parser(value)
        elif type_ in integer_types:
            value = integer_parser(value)
        elif type_ in floating_point_types:
            value = floating_point_parser(value)
        else:
            try:
                value = integer_parser(value)
            except ValueError:
                try:
                    value = floating_point_parser(value)
                except ValueError:
                    # Not a numerical value, do nothing
                    pass
        return value

    if isinstance(data, bytes):
        data = data.splitlines()

    protocol = {}
    for line in data:
        match = re.match(br"^(?P<key>[\w\[\]\.]+)\s+=\s+(?P<value>.*)$", line)
        key, value = match.groupdict()["key"], match.groupdict()["value"]

        entry = protocol
        for element in key.split(b"."):
            match = re.match(
                r"(a?)((?:{0})?)(\w+)(?:\[(\d+)\])?".format("|".join(types)).encode(), 
                element)
            is_array, type_, name, index = match.groups()

            full_name = "{}{}{}".format(is_array.decode(), type_.decode(), name.decode())

            is_array = (is_array == b"a")
            if index:
                index = int(index)

            if is_array:
                entry = entry.setdefault(full_name, [])

                if len(entry) <= index:
                    entry.extend((1+index-len(entry))*[None])
                if type_ not in (b"", b"s"):
                    entry[index] = value_parser(type_, value)
                else:
                    if entry[index] is None:
                        entry[index] = {}
                    entry = entry[index]
            elif type_ == b"s":
                entry = entry.setdefault(full_name, {})
            else:
                entry.setdefault(full_name, value_parser(type_, value))

    return protocol
