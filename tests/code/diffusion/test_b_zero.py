import inspect
import os
import tempfile
import unittest
import shutil

import erwin

from module_and_cli_test_case import ModuleAndCLITestCase

class TestBZeroNoAverage(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        self.cli_module = "diffusion.b_zero"
        self.class_ = erwin.diffusion.BZero
        self.arguments = {
            "source": os.path.join(self.baseline_path, "diffusion/dwi.mif.gz"),
            "target": os.path.join(self.directory, "target.nii")
        }
        self.baseline = os.path.join(
            self.baseline_path, "diffusion/b_zero_all.nii.gz")
        self.result = self.arguments["target"]
    
    def tearDown(self):
        shutil.rmtree(self.directory)

class TestBZeroWithAverage(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        self.cli_module = "diffusion.b_zero"
        self.class_ = erwin.diffusion.BZero
        self.arguments = {
            "source": os.path.join(self.baseline_path, "diffusion/dwi.mif.gz"),
            "target": os.path.join(self.directory, "target.nii"),
            "average": True
        }
        self.baseline = os.path.join(
            self.baseline_path, "diffusion/b_zero_average.nii.gz")
        self.result = self.arguments["target"]
    
    def tearDown(self):
        shutil.rmtree(self.directory)
    
    def test_cli(self):
        self.arguments["average"] = inspect.Parameter.empty
        ModuleAndCLITestCase.test_cli(self)

if __name__ == "__main__":
    unittest.main()
