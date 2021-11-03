import itertools
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

class TestbSSFP(ModuleAndCLITestCase, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        ModuleAndCLITestCase.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        
        sources = []
        flip_angles = []
        phase_increments = []
        repetition_times = []
        for flip_angle, phi in itertools.product([11, 58], [45, 135, 225, 315]):
            template = os.path.join(
                self.input_path, "bSSFP", "fa_{}_deg_phi_{}_deg.{}")
            with open(template.format(flip_angle, phi, "json")) as fd:
                meta_data = json.load(fd)
            sources.append(template.format(flip_angle, phi, "nii.gz"))
            flip_angles.append((meta_data["FlipAngle"][0]*deg).magnitude)
            phase_increments.append(
                (
                    erwin.meta_data.get_meta_data(
                        meta_data,
                        "00291020.0.MrPhoenixProtocol.0.sWiPMemBlock.alFree.5"
                    )*deg
                ).magnitude)
            repetition_times.append((meta_data["RepetitionTime"][0]*ms).magnitude)
        
        self.cli_module = "t2_map.bssfp"
        self.class_ = erwin.t2_map.bSSFP
        self.arguments = {
            "sources": sources,
            "flip_angles": flip_angles, "phase_increments": phase_increments,
            "repetition_time": repetition_times[0],
            "B1_map": os.path.join(
                self.baseline_path, "b1_map/xfl_in_bSSFP.nii.gz"),
            "T1_map": os.path.join(
                self.baseline_path, "t1_map/vfa_in_bSSFP.nii.gz"),
            "target": os.path.join(self.directory, "target.nii")
        }
        self.baseline = os.path.join(self.baseline_path, "t2_map/bssfp.nii.gz")
        self.result = self.arguments["target"]

if __name__ == "__main__":
    unittest.main()
