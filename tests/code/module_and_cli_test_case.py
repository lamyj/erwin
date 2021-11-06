import gzip
import inspect
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
                for name, value in self.arguments.items()
                if value is not inspect.Parameter.empty),
            *[
                ModuleAndCLITestCase._to_cli(name)
                for name, value in self.arguments.items()
                if value is inspect.Parameter.empty]])
        self._compare()
    
    def _compare(self):
        baseline, baseline_header = ModuleAndCLITestCase.load(self.baseline)
        result, result_header = ModuleAndCLITestCase.load(self.result)
        
        numpy.testing.assert_allclose(baseline.affine, result.affine)
        numpy.testing.assert_allclose(
            numpy.array(result.dataobj), numpy.array(baseline.dataobj),
            equal_nan=True)
        
        self.assertEqual(baseline_header is not None, result_header is not None)
        if baseline_header is not None:
            name = b"dw_scheme"
            self.assertEqual(name in baseline_header, name in result_header)
            if name in baseline_header:
                baseline_value = baseline_header[name]
                result_value = result_header[name]
                numpy.testing.assert_allclose(baseline_value, result_value)
            
            name = b"pe_scheme"
            self.assertEqual(name in baseline_header, name in result_header)
            self.assertTrue(all(baseline_header[name] == result_header[name]))
    
    @staticmethod
    def _to_cli(name):
        return "--{}".format(name.replace("_", "-"))
    
    @staticmethod
    def _to_string(value):
        if isinstance(value, (list, tuple)):
            return [ModuleAndCLITestCase._to_string(x)[0] for x in value]
        else:
            return [str(value)]
    
    @staticmethod
    def load(path):
        if path.endswith(".nii.gz") or path.endswith(".nii"):
            return nibabel.load(path), None
        elif path.endswith(".mif"):
            with open(path, "rb") as fd:
                return erwin.diffusion.mif_io.read(fd)
        elif path.endswith(".mif.gz"):
            with gzip.open(path, "rb") as fd:
                return erwin.diffusion.mif_io.read(fd)
