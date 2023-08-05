import base64
import json
import pathlib
import re
import subprocess
import tempfile

import dicomifier
import nibabel
import numpy
import spire

class BrukerToMIF(spire.TaskFactory):
    """ Convert DWI data from Bruker to MIF format.
    """
    
    def __init__(self, source: str, target: str):
        """ :param source: Path to DWI data in Bruker format
            :param target: Path to target DWI image in MIF format
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        self.file_dep = [source, meta_data]
        self.targets = [target]
        self.actions = [(BrukerToMIF.action, (source, meta_data, target))]
    
    @staticmethod
    def action(source_path, meta_data_path, target_path):
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        scheme = dicomifier.nifti.diffusion.from_standard(meta_data)
        
        bruker = json.loads(
            base64.b64decode(meta_data["EncapsulatedDocument"][0]).strip(b"\0"))
        method = dicomifier.bruker.Dataset()
        method.loads(bruker["method"])
        acqp = dicomifier.bruker.Dataset()
        acqp.loads(bruker["acqp"])
        
        pe_direction = acqp["ACQ_scaling_phase"].value[0]
        
        epi_factor = meta_data["EchoTrainLength"][0]
        echo_spacing = 1e-3 * method["PVM_EpiEchoSpacing"].value[0]
        total_readout_time = epi_factor*echo_spacing
        
        # NOTE: phase encoding table must be in image space
        phase_gradient = (
            numpy.around(
                numpy.reshape(method["PVM_SPackArrGradOrient"].value, (3,3))[1]
            ).astype(int))
        phase_gradient = numpy.abs(phase_gradient)
        
        image = nibabel.load(source_path)
        phase_encoding = numpy.array(
            image.shape[3]*[
                [*(pe_direction*phase_gradient), total_readout_time]])
        
        with tempfile.TemporaryDirectory() as dir:
            dir = pathlib.Path(dir)
            
            scheme_path = dir/"grad"
            with open(scheme_path, "w") as fd:
                dicomifier.nifti.diffusion.to_mrtrix(scheme, fd)
            
            pe_path = dir/"pe"
            numpy.savetxt(pe_path, phase_encoding, "%g")
            subprocess.check_call([
                "mrconvert", "-quiet", "-force", source_path,
                "-grad", scheme_path, "-import_pe_table", pe_path,
                target_path])

def main():
    return entrypoint(BrukerToMIF)
