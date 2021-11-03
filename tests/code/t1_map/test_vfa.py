import json
import os
import tempfile
import unittest
import shutil

import nibabel
import numpy
from sycomore.units import *

import erwin

from module_and_cli_test_case import ModuleAndCLITestCase

class TestVFA(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        template = os.path.join(self.input_path, "GRE", "{}_deg_magnitude.{}")
        
        sources = []
        flip_angles = []
        echo_times = []
        repetition_times = []
        
        for flip_angle in 6, 32:
            image = nibabel.load(template.format(flip_angle, "nii.gz"))
            data = numpy.array(image.dataobj)
            source = os.path.join(
                self.directory, "{}.nii.gz".format(flip_angle))
            nibabel.save(
                nibabel.Nifti1Image(data[..., 1], image.affine), source)
            sources.append(source)
            
            with open(template.format(flip_angle, "json")) as fd:
                meta_data = json.load(fd)
            flip_angles.append((meta_data["FlipAngle"][0]*deg).magnitude)
            echo_times.append((meta_data["EchoTime"][1][0]*ms).magnitude)
            repetition_times.append(
                (meta_data["RepetitionTime"][0]*ms).magnitude)
        
        self.cli_module = "t1_map.vfa"
        self.class_ = erwin.t1_map.VFA
        self.arguments = {
            "sources": sources,
            "flip_angles": flip_angles,
            "echo_time": echo_times[0], "repetition_time": repetition_times[0],
            "B1_map": os.path.join(
                self.baseline_path, "b1_map/xfl_in_GRE.nii.gz"),
            "target": os.path.join(self.directory, "target.nii")
        }
        self.baseline = os.path.join(self.baseline_path, "t1_map/vfa.nii.gz")
        self.result = self.arguments["target"]
    
    def tearDown(self):
        shutil.rmtree(self.directory)

if __name__ == "__main__":
    unittest.main()
