import base64
import itertools
import json
import os
import re
import struct

import dicomifier
import numpy
import spire

from .. import entrypoint, parsing

class SiemensToMIF(spire.TaskFactory):
    """ Convert DWI data from Siemens to MIF format.
    """
    
    def __init__(self, sources, target):
        spire.TaskFactory.__init__(self, str(target))
    
        meta_data = [
            re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        
        target_dir = os.path.dirname(target)
        target_base = os.path.basename(target)
        
        temp = os.path.join(target_dir, "__{}_temp.mif".format(target_base))
        diffusion_scheme_path = os.path.join(
            target_dir, "__{}.diff".format(target_base))
        phase_encoding_scheme_path = os.path.join(
            target_dir, "__{}.pe".format(target_base))
    
        self.file_dep = list(itertools.chain(sources, meta_data))
        self.targets = [target]
        self.actions = [
            ["mrcat", "-force", "-quiet"] + sources + [temp],
            (
                SiemensToMIF.diffusion_scheme, 
                (meta_data, diffusion_scheme_path)),
            (
                SiemensToMIF.phase_encoding_scheme, 
                (meta_data, phase_encoding_scheme_path)),
            [
                "mrconvert", "-force",
                "-grad", diffusion_scheme_path, 
                "-import_pe_table", phase_encoding_scheme_path,
                temp, target],
            ["rm", temp, diffusion_scheme_path, phase_encoding_scheme_path]
        ]
    
    @staticmethod
    def diffusion_scheme(meta_data_paths, scheme_path):
        scheme = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data = json.load(fd)
            scheme.extend(
                dicomifier.nifti.diffusion.from_siemens_csa(meta_data))
        with open(scheme_path, "w") as fd:
            dicomifier.nifti.diffusion.to_mrtrix(scheme, fd)
    
    @staticmethod
    def phase_encoding_scheme(meta_data_paths, scheme_path):
        scheme = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data = json.load(fd)
            
            if isinstance(meta_data["00191028"][0], float):
                bandwidth_per_pixel_phase = meta_data["00191028"][0]*1e3
            else:
                bandwidth_per_pixel_phase = struct.unpack(
                        "d", base64.b64decode(meta_data["00191028"][0])
                    )[0]*1e3
            effective_echo_spacing = 1/bandwidth_per_pixel_phase
            phase_size = meta_data["AcquisitionMatrix"][
                2 if meta_data["InPlanePhaseEncodingDirection"][0]=="ROW" else 3]
            # In seconds
            total_readout_time = (phase_size - 1) * effective_echo_spacing
    
            csa = [
                dicomifier.dicom_to_nifti.siemens.parse_csa(
                    base64.b64decode(x[0] if len(x[0])>4 else x))
                for x in meta_data["00291010"]]
            axis = (
                [1,0,0] if meta_data["InPlanePhaseEncodingDirection"][0] == "ROW" 
                else [0,1,0])
            # WARNING: PhaseEncodingDirectionPositive is in LPS
            signs = [
                -1 if x["PhaseEncodingDirectionPositive"][0] == 1 else +1
                for x in csa]
            scheme.extend([
                [sign*x for x in axis]+[total_readout_time] for sign in signs])
        
        # WARNING: Eddy complains when the total readout time is either too 
        # small or too large. Rescale our values in FSL's range.
        # https://salsa.debian.org/neurodebian-team/fsl/blob/master/src/eddy/EddyHelperClasses.cpp#L52
        scheme = numpy.asarray(scheme)
        readout_time = scheme[:, -1]
        source_range = (readout_time.max()-readout_time.min()) or 1
        readout_time = (
            0.01 + (0.2-0.01)/source_range * (readout_time-readout_time.min()))
        scheme[:, -1] = readout_time

        numpy.savetxt(str(scheme_path), scheme)

def main():
    return entrypoint(
        SiemensToMIF, [
            parsing.Multiple([
                "--sources", {"help": "Diffusion-weighted image"}]),
            (
                "--target",
                {"help": "Path to the target DWI image in MIF format"})])
