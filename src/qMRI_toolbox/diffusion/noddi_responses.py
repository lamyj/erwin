import io
import os
import subprocess

import amico
import numpy
import spire

from .. import entrypoint

class NODDIResponses(spire.TaskFactory):
    def __init__(
            self, scheme, response_directory, 
            shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        spire.TaskFactory.__init__(self, str(response_directory))
        self.file_dep = [scheme]
        
        model = amico.models.NODDI()
        self.targets = [
            os.path.join(response_directory, "A_{:03}.npy".format(1+x))
            for x in range(1+len(model.IC_ODs)*len(model.IC_VFs))]
        self.actions = [
            ["mkdir", "-p", response_directory],
            (
                NODDIResponses.responses, 
                (scheme, response_directory, shell_width, b0_threshold, lmax, ndirs))
        ]
    
    @staticmethod
    def responses(
            dwi, response_directory, 
            shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        amico.core.setup(lmax, ndirs)
        
        scheme = subprocess.check_output(["mrinfo", "-dwgrad", dwi])
        # NOTE Amico expects x,y,z (which frame?), b-value (s/mm^2)
        scheme = numpy.loadtxt(io.BytesIO(scheme))
        # NOTE Amico expects shelled data
        if shell_width != 0:
            scheme[:,3] = numpy.round(scheme[:,3]/shell_width)*shell_width
        scheme = amico.scheme.Scheme(scheme, b0_threshold)
        
        rotation_matrices = amico.lut.load_precomputed_rotation_matrices(
            lmax, ndirs)
        shells, harmonics = amico.lut.aux_structures_generate(scheme, lmax)
        
        model = amico.models.NODDI()
        model.scheme = scheme
        model.generate(
            response_directory, rotation_matrices, shells, harmonics, ndirs)

def main():
    return entrypoint(
        NODDIResponses, [
            ("dwi", {"help": "Diffusion-weighted image, in MRtrix format"}),
            ("response_directory", {"help": "Target response directory"}),
            (
                "--shell-width", {
                    "type":float, "default": 0, 
                    "help": "Width used to group the real b-values in ideal shells"}),
            (
                "--b0-threshold", {
                    "type":float, "default": 0, 
                    "help": "Lower b-value threshold"}),
            (
                "--lmax", {
                    "type":int, "default": 12,
                    "help": "Maximum order of spherical harmonics"}),
            (
                "--ndirs", {
                    "type": int, "default": 32761,
                    "help": "Number of directions on the hemisphere"})
        ])
