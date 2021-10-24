import os

import amico
import spire

from .. import entrypoint, parsing
from .noddi import NODDI

class NODDIResponses(spire.TaskFactory):
    """ Generate the response functions for the two NODDI compartments.
        
        This only depends on the diffusion-encoding scheme, and is based on
        AMICO.
    """
    
    def __init__(
            self, dwi, response_directory, 
            shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        spire.TaskFactory.__init__(self, str(response_directory))
        self.file_dep = [dwi]
        
        model = amico.models.NODDI()
        self.targets = [
            os.path.join(response_directory, "A_{:03}.npy".format(1+x))
            for x in range(1+len(model.IC_ODs)*len(model.IC_VFs))]
        self.actions = [
            ["mkdir", "-p", response_directory],
            (
                NODDIResponses.responses, 
                (dwi, response_directory, shell_width, b0_threshold, lmax, ndirs))
        ]
    
    @staticmethod
    def responses(
            dwi, response_directory, 
            shell_width=0, b0_threshold=0, lmax=12, ndirs=32761):
        
        amico.core.setup(lmax, ndirs)
        
        scheme = NODDI.amico_scheme(dwi, shell_width, b0_threshold)
        
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
            ("--dwi", {"help": "Diffusion-weighted image, in MRtrix format"}),
            ("--response-directory", {"help": "Target response directory"}),
            parsing.Optional([
                "--shell-width", {
                    "type":float, "default": 0, 
                    "help": "Width used to group the real b-values in ideal shells"}]),
            parsing.Optional([
                "--b0-threshold", {
                    "type":float, "default": 0, 
                    "help": "Lower b-value threshold"}]),
            parsing.Optional([
                "--lmax", {
                    "type":int, "default": 12,
                    "help": "Maximum order of spherical harmonics"}]),
            parsing.Optional([
                "--ndirs", {
                    "type": int, "default": 32761,
                    "help": "Number of directions on the hemisphere"}])
        ])
