import json
import os
import unittest
import subprocess
import sys

import erwin

from module_and_cli_test_case import ModuleAndCLITestCase

class TestGet(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.path = os.path.join(self.input_path, "GRE", "6_deg_magnitude.json")
    
    def test_module(self):
        
        with open(self.path) as fd:
            meta_data = json.load(fd)
        
        self.assertEqual(
            erwin.meta_data.get_meta_data(meta_data, "EchoTime.1.0"), 6.9)
        self.assertEqual(
            erwin.meta_data.get_meta_data(
                meta_data, "00291010.0.0.0.ImaAbsTablePosition"), [0, 0, -1071])
        self.assertEqual(
            erwin.meta_data.get_meta_data(
                meta_data, "00291020.0.MrPhoenixProtocol.0.alTR"), [28000])
    
    def test_cli(self):
        command = [
            sys.executable, "-m", "erwin",
            "meta_data.get", "-p", self.path, "-q"]
        
        get_output = lambda x: subprocess.check_output(command+[x]).strip()
        
        self.assertEqual(get_output("EchoTime.1.0"), b"6.9")
        self.assertEqual(
            get_output("00291010.0.0.0.ImaAbsTablePosition.2"), b"-1071")
        self.assertEqual(
            get_output("00291020.0.MrPhoenixProtocol.0.alTR.0"), b"28000")
    
    
if __name__ == "__main__":
    unittest.main()
