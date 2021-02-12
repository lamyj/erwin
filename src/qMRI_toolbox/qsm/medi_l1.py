import json
import os
import re

import meg
import nibabel
import numpy
import spire

from .. import entrypoint

class MediL1(spire.TaskFactory):
    def __init__(
            self, magnitude, total_field, sd_noise, object_field, brain, 
            ventricles, target, medi_toolbox, meta_data=None):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(magnitude))
        
        self.file_dep = [
            magnitude, total_field, object_field, brain, ventricles, meta_data]
        self.targets = [target]
        
        self.actions = [
            (
                MediL1.medi, (
                    magnitude, total_field, sd_noise, object_field, brain, 
                    ventricles, meta_data, target, medi_toolbox))]
    
    @staticmethod
    def medi(
            magnitude_path, total_field_path, sd_noise_path, object_field_path,
            brain_path, ventricles_path, meta_data_path, target_path,
            medi_toolbox_path):
        
        magnitude = nibabel.load(magnitude_path)
        total_field = nibabel.load(total_field_path)
        sd_noise = nibabel.load(sd_noise_path)
        object_field = nibabel.load(object_field_path)
        brain = nibabel.load(brain_path)
        ventricles = nibabel.load(ventricles_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        echo_times = [1e-3*x[0] for x in meta_data["EchoTime"]]
        echo_spacing = numpy.diff(echo_times).mean()
        
        imaging_frequency = 1e6 * meta_data["ImagingFrequency"][0]
        
        with meg.Engine() as engine:
            engine(f"run('{medi_toolbox_path}/MEDI_set_path.m');")
            
            # file must contain
            engine["iMag"] = magnitude.get_fdata().sum(axis=-1)
            engine["iFreq"] = total_field.get_fdata()
            engine["N_std"] = sd_noise.get_fdata()
            engine["RDF"] = object_field.get_fdata()
            engine["Mask"] = brain.get_fdata()
            engine["Mask_CSF"] = ventricles.get_fdata()
            
            engine["matrix_size"] = numpy.array(magnitude.shape[:3], float)
            engine["voxel_size"] = magnitude.header["pixdim"][1:1+magnitude.ndim]
            engine["delta_TE"] = echo_spacing
            engine["CF"] = imaging_frequency
            # WARNING: this assumes an axial reconstruction of the data
            engine["B0_dir"] = magnitude.affine[:3, :3] @ [0,0,1]
            
            RDF_mat = os.path.join(os.path.dirname(target_path), "RDF.mat")
            engine(
                "save("
                    f"'{RDF_mat}', 'RDF', 'iFreq', 'iMag', 'N_std', "
                    "'Mask', 'matrix_size', 'voxel_size', 'delta_TE', 'CF', "
                    "'B0_dir', 'Mask_CSF');")
            
            engine(
                "QSM = MEDI_L1("
                    f"'filename', '{RDF_mat}', "
                    "'lambda', 1000, 'lambda_CSF', 100, 'merit', 'smv', 5);")
            
            os.unlink(RDF_mat)
            
            QSM = engine["QSM"]
            nibabel.save(nibabel.Nifti1Image(QSM, magnitude.affine), target_path)

def main():
    return entrypoint(
        MediL1, [
            ("magnitude", {"help": "Multi-echo magnitude image"}),
            ("total_field", {"help": "Total susceptibility field"}),
            (
                "sd_noise", {
                    "help": "Standard deviation of noise "
                        "in total susceptibility field"}),
            ("object_field", {"help": "Foreground susceptibility field"}),
            ("brain", {"help": "Brain mask"}),
            ("ventricles", {"help": "Ventricles mask"}),
            ("target", {"help": "Total field image"}),
            (
                "--medi", {
                    "required": True, 
                    "dest": "medi_toolbox", 
                    "help": "Path to the MEDI toolbox"})])
