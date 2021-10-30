import base64
import itertools
import json
import os
import re
import struct
import tempfile

import dicomifier
import nibabel
import numpy
import spire

from .. import entrypoint

class BrukerToMIF(spire.TaskFactory):
    """ Convert DWI data from Bruker to MIF format.
    """
    
    def __init__(self, source, target):
        spire.TaskFactory.__init__(self, str(target))
    
        meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        target_dir = os.path.dirname(target)
        target_base = os.path.basename(target)
        
        diffusion_scheme_path = os.path.join(
            target_dir, "__{}.diff".format(target_base))
        phase_encoding_scheme_path = os.path.join(
            target_dir, "__{}.pe".format(target_base))
    
        self.file_dep = [source, meta_data]
        self.targets = [target]
        self.actions = [
            (
                BrukerToMIF.diffusion_scheme, 
                (meta_data, diffusion_scheme_path)),
            (
                BrukerToMIF.phase_encoding_scheme, 
                (source, meta_data, phase_encoding_scheme_path)),
            [
                "mrconvert", "-force",
                "-grad", diffusion_scheme_path, 
                "-import_pe_table", phase_encoding_scheme_path,
                source, target],
            ["rm", diffusion_scheme_path, phase_encoding_scheme_path]
        ]
    
    @staticmethod
    def diffusion_scheme(meta_data_path, scheme_path):
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        scheme = dicomifier.nifti.diffusion.from_standard(meta_data)
        with open(scheme_path, "w") as fd:
            dicomifier.nifti.diffusion.to_mrtrix(scheme, fd)
    
    @staticmethod
    def phase_encoding_scheme(source_path, meta_data_path, scheme_path):
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        bruker_data = json.loads(
            base64.b64decode(meta_data["EncapsulatedDocument"][0]))
        
        # acqp = dicomifier.bruker.Dataset()
        # with tempfile.NamedTemporaryFile("w") as fd:
        #     fd.write(bruker_data["acqp"])
        #     acqp.load(fd.name)
        # # NOTE: ACQ_grad_matrix is "independent of the patient orientation"
        # # (D02_PvParams.pdf, p. D-2-36)
        # gradients = numpy.reshape(acqp["ACQ_grad_matrix"].value, (-1, 3, 3))
        # phase_directions = gradients[:,1]
        
        method = dicomifier.bruker.Dataset()
        with tempfile.NamedTemporaryFile("w") as fd:
            fd.write(bruker_data["method"])
            method.load(fd.name)
        # NOTE: is this still valid for multi-shot data?
        # cf. PVM_EpiNShots
        total_readout_time = 1e-3*(
            (method["PVM_EpiNEchoes"].value[0]-1) 
            * method["PVM_EpiEchoSpacing"].value[0])
        
        phase_gradient = numpy.around(
            numpy.reshape(method["PVM_SPackArrGradOrient"].value, (3,3))[1])
        
        entry = numpy.hstack((phase_gradient, [total_readout_time]))
        
        # WARNING: the phase direction is in the *image* space, each component
        # is expected to be -1, 0 or +1
        # https://github.com/MRtrix3/mrtrix3/blob/3.0.2/core/phase_encoding.h#L55-L56
        # https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/Faq#How_do_I_know_what_to_put_into_my_--acqp_file
        scheme = numpy.tile(entry, (nibabel.load(source_path).shape[-1], 1))
        
        # WARNING: Eddy complains when the total readout time is either too 
        # small or too large. Rescale our values in FSL's range.
        # https://salsa.debian.org/neurodebian-team/fsl/blob/master/src/eddy/EddyHelperClasses.cpp#L52
        readout_time = scheme[:, -1]
        source_range = (readout_time.max()-readout_time.min()) or 1
        readout_time = (
            0.01 + (0.2-0.01)/source_range * (readout_time-readout_time.min()))
        scheme[:, -1] = readout_time

        numpy.savetxt(str(scheme_path), scheme)

def main():
    return entrypoint(
        BrukerToMIF, [
            ("--source", {"help": "Diffusion-weighted image"}),
            (
                "--target",
                {"help": "Path to the target DWI image in MIF format"})])
