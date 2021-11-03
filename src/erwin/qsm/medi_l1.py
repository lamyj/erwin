import os

import nibabel
import numpy
import spire

from .. import entrypoint, parsing

class MediL1(spire.TaskFactory):
    """ Compute the QSM using the MEDI+0 method of the MEDI toolbox.
        
        Reference: MEDI+0: Morphology enabled dipole inversion with automatic 
        uniform cerebrospinal fluid zero reference for quantitative 
        susceptibility mapping. Liu et al. Magnetic Resonance in Medicine 79(5).
        2018
    """
    
    def __init__(
            self, magnitude, imaging_frequency, echo_times, total_field, 
            sd_noise, object_field, brain, ventricles, target, medi_toolbox):
        """ :param str magnitude: Path to magnitude image
            :param float imaging_frequency: Resonance frequency used by the \
                scanner (Hz)
            :param Sequence(float) echo_times,te: Echo times (s)
            :param str total_field: Path to map of total susceptibility field
            :param str sd_noise: Path map of standard deviation of noise in \
                total susceptibility field
            :param str object_field: Path to foreground susceptibility field
            :param str brain: Path to binary brain mask
            :param str ventricles: Path to binary ventricles mask
            :param str target: Path to target susceptibility map
            :param str medi_toolbox,medi: Path to the MEDI toolbox
        """
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [
            magnitude, total_field, object_field, brain, ventricles]
        self.targets = [target]
        
        self.actions = [
            (
                MediL1.medi, (
                    magnitude, imaging_frequency, echo_times, total_field,
                    sd_noise, object_field, brain, ventricles, target,
                    medi_toolbox))]
    
    @staticmethod
    def medi(
            magnitude_path, imaging_frequency, echo_times, total_field_path,
            sd_noise_path, object_field_path, brain_path, ventricles_path,
            target_path, medi_toolbox_path):
        
        import meg
        
        magnitude = nibabel.load(magnitude_path)
        total_field = nibabel.load(total_field_path)
        sd_noise = nibabel.load(sd_noise_path)
        object_field = nibabel.load(object_field_path)
        brain = nibabel.load(brain_path)
        ventricles = nibabel.load(ventricles_path)
        
        echo_spacing = numpy.diff(echo_times).mean()
        
        with meg.Engine() as engine:
            engine("run('{}/MEDI_set_path.m');".format(medi_toolbox_path))
            
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
                (
                    "save("
                        "'{}', 'RDF', 'iFreq', 'iMag', 'N_std', "
                        "'Mask', 'matrix_size', 'voxel_size', 'delta_TE', 'CF', "
                        "'B0_dir', 'Mask_CSF');"
                ).format(RDF_mat))
            
            engine(
                (
                    "QSM = MEDI_L1("
                        "'filename', '{}', "
                        "'lambda', 1000, 'lambda_CSF', 100, 'merit', 'smv', 5);"
                ).format(RDF_mat))
            
            os.unlink(RDF_mat)
            
            QSM = engine["QSM"]
            nibabel.save(nibabel.Nifti1Image(QSM, magnitude.affine), target_path)

def main():
    return entrypoint(MediL1)
