import argparse
import json
import re

import nibabel

def image_type(string):
    try:
        image = nibabel.load(string)
    except Exception as e:
        raise argparse.ArgumentTypeError(e)
    return image

def image_and_meta_data_type(string):
    try:
        image = nibabel.load(string)
        meta_data_path = re.sub(r"\.nii(\.gz)?$", ".json", string)
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
    except Exception as e:
        raise argparse.ArgumentTypeError(e)
    
    return image, meta_data
