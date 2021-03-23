import re
import subprocess
import tempfile

import numpy
import nibabel

def read(path_or_fd):
    """ Read a MIF-format file from a filesystem path or an opened file 
        descriptor.
    """
    
    if hasattr(path_or_fd, "read"):
        path = getattr(path_or_fd, "name", None)
        fd = path_or_fd
    else:
        path = path_or_fd
        fd = open(path, "rb")
    header = read_header(fd)
    
    # FIXME MRtrix seems to apply extra transforms when converting to NIfTI
    # (probably LPS to RAS). Until this is fixed, use a slower version based on
    # mrconvert and temporary files
    # if header[b"file"][0] == b".":
    #     fd.seek(0)
    #     buffer = read_buffer(header, fd)
    # else:
    #     with open(header[b"file"][0], "rb") as buffer_fd:
    #         buffer = read_buffer(header, buffer_fd)
    # 
    # affine = get_affine(header)
    # image = nibabel.Nifti1Image(buffer, affine)
    
    with tempfile.NamedTemporaryFile(suffix=".nii") as fd:
        subprocess.check_call(["mrconvert", "-quiet", "-force", path, fd.name])
        # Load the image and convert the proxy array to a real array
        image = nibabel.load(fd.name)
        image = nibabel.Nifti1Image(
            numpy.array(image.dataobj), image.affine, image.header)
    
    for x in [b"dim", b"vox", b"layout", b"datatype", b"file", b"transform"]:
        del header[x]
    
    return image, header

def read_header(fd):
    """ Return a dictionary of fields from a MIF header.
    """
    
    magic = fd.readline().strip()
    if magic != b"mrtrix image":
        raise Exception("Invalid file")
    header = {}
    line = b""
    while line.strip() != b"END":
        line = fd.readline().strip()
        if line == b"END":
            continue
        key, value = line.split(b": ", 1)
        if key in [b"dim", b"layout"]:
            value = numpy.array([int(x) for x in value.split(b",")])
        elif key in [b"vox", b"transform", b"dw_scheme", b"prior_pe_scheme"]:
            value = numpy.array([float(x) for x in value.split(b",")])
        elif key == b"file":
            name, offset = re.match(br"(.*) (\d+)", value).groups()
            offset = int(offset)
            value = name, offset
        header.setdefault(key, []).append(value)
    
    for key in [b"dim", b"vox", b"layout", b"datatype", b"file"]:
        header[key] = header[key][0]
    
    for key in [
            b"transform", b"dw_scheme", b"pe_scheme",
            b"prior_dw_scheme", b"prior_pe_scheme"]:
        if key in header:
            header[key] = numpy.array(header[key])
    
    return header

def read_buffer(header, fd):
    dtype = get_dtype(header)
    offset = header[b"file"][1]
    dim, layout = [header[x] for x in [b"dim", b"layout"]]
    
    buffer = numpy.frombuffer(fd.read(), dtype, offset=offset)
    
    # Reshape the data. Use Fortran order as layout notes the shortest
    # stride as 0
    order = numpy.argsort(numpy.abs(layout))
    buffer = buffer.reshape(dim[order], order="F")
    # Rearrange the axes according to the layout, flip if needed
    buffer = buffer.transpose(numpy.abs(layout))
    for index, axis in enumerate(layout):
        if axis < 0:
            buffer = numpy.flip(buffer, index)
    
    return buffer

def get_affine(header):
    """ Return the affine matrix contained in a MIF header.
    """
    
    transform = header[b"transform"]
    vox = header[b"vox"]
    affine = numpy.vstack([numpy.array(transform), [0,0,0,1]]) @ numpy.diag(vox)
    return affine

def get_dtype(header):
    """ Return the numpy dtype matching the MIF header.
    """
    
    data_type = header[b"datatype"].lower()
    data_type_regex = re.compile(br"^(bit|int|uint|float|cfloat)(\d+)?(le|be)?$")
    kind, width_bits, endianness = re.match(data_type_regex, data_type).groups()
    
    kind = {
            b"int": "i",
            b"uint": "u",
            b"float": "f",
            b"cfloat": "c",
        }[kind]
    width = int(width_bits)//8
    endianness = {
        None: "",
        b"le": "<",
        b"be": ">"
        }[endianness]
    return numpy.dtype("{}{}{}".format(endianness, kind, width))
