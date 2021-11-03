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

class TestDoubleEcho(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
        
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        magnitude_path = os.path.join(self.input_path, "GRE", "32_deg_magnitude")
        phase_path = os.path.join(self.input_path, "GRE", "32_deg_phase")
        
        with open("{}.json".format(magnitude_path)) as fd:
            meta_data = json.load(fd)
        
        image = nibabel.load("{}.nii.gz".format(magnitude_path))
        data = numpy.array(image.dataobj)
        magnitude_path = os.path.join(self.directory, "magnitude_")
        for index in [0, 1]:
            nibabel.save(
                nibabel.Nifti1Image(data[..., index], image.affine),
                "{}{}.nii".format(magnitude_path, index))
        
        image = nibabel.load("{}.nii.gz".format(phase_path))
        data = numpy.array(image.dataobj)
        phase_path = os.path.join(self.directory, "phase_")
        for index in [0, 1]:
            nibabel.save(
                nibabel.Nifti1Image(data[..., index]/4096*numpy.pi, image.affine),
                "{}{}.nii".format(phase_path, index))
        
        self.cli_module = "b0_map.double_echo"
        self.class_ = erwin.b0_map.DoubleEcho
        self.arguments = {
            "magnitude": ["{}{}.nii".format(magnitude_path, x) for x in [0, 1]],
            "phase": ["{}{}.nii".format(phase_path, x) for x in [0, 1]],
            "echo_times": [(x[0]*ms).magnitude for x in meta_data["EchoTime"]],
            "target": os.path.join(self.directory, "target.nii")
        }
        self.baseline = os.path.join(
            self.baseline_path, "b0_map/double_echo.nii.gz")
        self.result = self.arguments["target"]
        
    def tearDown(self):
        shutil.rmtree(self.directory)
    
if __name__ == "__main__":
    unittest.main()
