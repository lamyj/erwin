import argparse
import base64
import itertools
import json
import re
import sys

import dicomifier
import nibabel
import numpy
import spire

from . import common

class MTR(spire.TaskFactory):
    """ Compute the MT ratio (i.e. (MT_off - MT_on) / MT_off) of two images.
        The sources images can be supplied in any order, they will be sorted
        before computing the ratio.
    """
    
    def __init__(self, sources, target, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        self.sources = sources
        
        if meta_data is None:
            meta_data = [
                re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        self.meta_data = meta_data
        
        self.file_dep = list(itertools.chain(sources, meta_data))
        self.targets = [target]
        
        self.actions = [(MTR.mtr_map, (sources, meta_data, target))]
    
    @staticmethod
    def mtr_map(source_paths, meta_data_paths, mtr_map_path):
        meta_data_array = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data_array.append(json.load(fd))
        
        MT_off_path, MT_on_path = None, None
        for source_path, meta_data in zip(source_paths, meta_data_array):
            pulses = common.get_pulses(meta_data)
            
            if len(pulses) == 1:
                MT_off_path = source_path
            elif len(pulses) == 2:
                MT_on_path = source_path
        
        MT_off = nibabel.load(MT_off_path)
        MT_on = nibabel.load(MT_on_path)
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            MT_off_array = MT_off.get_fdata()
            MT_on_array = MT_on.get_fdata()
            # If we have multiple echoes, average them
            if len(meta_data_array[0]["EchoTime"]) > 1:
                MT_off_array = MT_off_array.mean(axis=-1)
                MT_on_array = MT_on_array.mean(axis=-1)
            MTR = 1 - MT_on_array / MT_off_array
        
        MTR[MTR<0] = 0
        MTR[MTR>1] = 1
        
        nibabel.save(nibabel.Nifti1Image(MTR, MT_off.affine), mtr_map_path)

def main():
    parser = argparse.ArgumentParser(description=MTR.__doc__)
    parser.add_argument(
        "sources", nargs=2,
        help="SPGR images with and without MT pulse (in any order)")
    parser.add_argument("target", help="Path to the target MTR map")
    arguments = parser.parse_args()
    
    task = MTR(**vars(arguments))
    MTR.mtr_map(task.sources, task.meta_data, *task.targets)
