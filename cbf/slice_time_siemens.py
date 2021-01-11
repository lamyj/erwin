import base64
import json
import re
import struct

import nibabel
import numpy
import spire

from .. import entrypoint

class SliceTimeSiemens(spire.TaskFactory):
    """ Create a slice-time image from Siemens private data.
    """
    
    def __init__(self, source, meta_data, target):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        self.actions = [
            (SliceTimeSiemens.get_slice_time, [source, meta_data, target])]
    
    def get_slice_time(source_path, meta_data_path, target_path):
        source = nibabel.load(source_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        slice_times = 1e-3 * numpy.asarray([
            struct.unpack("{}d".format(source.shape[2]), base64.b64decode(x[0])) 
            for x in meta_data["00191029"]]).T
        slice_times_array = numpy.tile(slice_times, source.shape[:2]+(1, 1))
        
        nibabel.save(
            nibabel.Nifti1Image(slice_times_array, source.affine), target_path)

def main():
    return entrypoint(
        SliceTimeSiemens, [
            ("source", {"help": "Source image"}),
            ("meta_data", {"nargs": "?", "help": "Source image meta-data"}),
            ("target", {"help": "Target slice-time image"})
        ])
