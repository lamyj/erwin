import os
import tempfile
import unittest
import shutil

import erwin

from module_and_cli_test_case import ModuleAndCLITestCase

class TestSiemensToMIF(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        self.cli_module = "diffusion.siemens_to_mif"
        self.class_ = erwin.diffusion.SiemensToMIF
        self.arguments = {
            "sources": [
                os.path.join(self.input_path, "DWI", "{}.nii.gz".format(x))
                for x in ["b0_PA", "b300_AP", "b700_AP", "b2000_AP"]],
            "target": os.path.join(self.directory, "target.mif")
        }
        self.baseline = os.path.join(self.baseline_path, "diffusion/dwi.mif.gz")
        self.result = self.arguments["target"]
    
    def tearDown(self):
        shutil.rmtree(self.directory)

if __name__ == "__main__":
    unittest.main()
