import itertools
import os
import subprocess
import sys

import nibabel
import numpy

import erwin

class ModuleAndCLITestCase(object):
    def __init__(self):
        self.data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data")
        self.input_path = os.path.join(self.data_path, "input")
        self.baseline_path = os.path.join(self.data_path, "baseline")
        
        self.cli_module = None
        self.class_ = None
        self.arguments = {}
        self.baseline = None
        self.result = None
    
    def test_module(self):
        task = self.class_(**self.arguments)
        erwin.run([task])
        self._compare()
    
    def test_cli(self):
        subprocess.check_call([
            sys.executable, "-m", "erwin", self.cli_module, "-v", "debug", 
            *itertools.chain.from_iterable(
                (
                    ModuleAndCLITestCase._to_cli(name),
                    *ModuleAndCLITestCase._to_string(value))
                for name, value in self.arguments.items())])
        self._compare()
    
    def _compare(self):
        baseline = nibabel.load(self.baseline)
        result = nibabel.load(self.result)
        
        numpy.testing.assert_allclose(baseline.affine, result.affine)
        numpy.testing.assert_allclose(
            numpy.array(result.dataobj), numpy.array(baseline.dataobj),
            equal_nan=True)
        
    
    @staticmethod
    def _to_cli(name):
        return "--{}".format(name.replace("_", "-"))
    
    @staticmethod
    def _to_string(value):
        if isinstance(value, (list, tuple)):
            return [ModuleAndCLITestCase._to_string(x)[0] for x in value]
        else:
            return [str(value)]
