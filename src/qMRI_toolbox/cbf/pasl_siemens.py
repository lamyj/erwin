import base64
import json
import re

import dicomifier
import nibabel
import numpy
import spire

from .. import entrypoint, misc

class pASLSiemens(spire.TaskFactory):
    """ Compute the CBF based on a pASL from Siemens.
        
        References:
        - Comparison of quantitative perfusion imaging using arterial spin 
          labeling at 1.5 and 4.0 Tesla. Wang et al. Magnetic Resonance in 
          Medicine 42(28). 2002.
        - Correcting for the echo-time effect after measuring the cerebral blood
          flow by arterial spin labeling. Foucher et al. Journal of Magnetic 
          Resonance Imaging 34(4). 2011.
    """
    
    def __init__(self, source, meta_data, slice_time, target):
        spire.TaskFactory.__init__(self, str(target))
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data, slice_time]
        self.targets = [target]
        
        self.actions = [
            (pASLSiemens.get_cbf, (source, meta_data, slice_time, target))]
    
    def get_cbf(source_path, meta_data_path, slice_time_path, target_path):
        source = nibabel.load(source_path)
        
        with open(meta_data_path) as fd:
            meta_data = json.load(fd)
        
        slice_time = nibabel.load(slice_time_path)
        
        csa_group = misc.siemens_csa.find_csa_group(meta_data) or 0x00291000
        csa = dicomifier.dicom_to_nifti.siemens.parse_csa(
            base64.b64decode(meta_data["{:08x}".format(csa_group+0x20)][0]))
        protocol = csa["MrPhoenixProtocol"][0]
        ascconv = re.search(
            b"### ASCCONV BEGIN ###\s+(.+)\s+### ASCCONV END ###", protocol, 
            flags=re.DOTALL).group(1).decode()

        # Blood/tissue water partition coefficient, in L/kg
        # - 0.9 mL/g in Wang et al. and Foucher et al. (global)
        # - 0.98 mL/g in Foucher (GM)
        # - 0.81 mL/g in Foucher (WM)
        lambda_ = 0.9 * 1e-3 / 1e-3

        # T₁ of blood in s (1.2 s at 1.5 T in Wang et al., 1.5 s at 3 T in 
        # Foucher et al.)
        T1_a = 1.5
        # Inversion efficiency (0.95 in both Wang et al. and Foucher et al.), 
        # unitless
        alpha = 0.95

        # Difference in the apparent transverse relaxation rates between labeled
        # water in capillaries and nonlabeled water in the tissue, in Hz
        # 23 Hz for white matter
        delta_R2_star = 20
        
        # Echo time in s
        TE = meta_data["EchoTime"][0]*1e-3

        # Inversion times, as defined in Wang et al., in seconds
        TI = re.findall(r"^a.TI\[\d+]\s+=\s+([\d.]+)", ascconv, flags=re.M)
        # Time between inversion and saturation
        TI_1 = float(TI[1]) / 1e6
        # Time between inversion and image acquisition of *first* slice
        TI_2 = float(TI[2]) / 1e6
        # Convert TI_2 to real slice acquistion time
        TI_2 = TI_2 + slice_time.get_fdata()
        # WARNING: slice timing may vary across volumes. Average the 
        # corresponding tagged/untagged volumes.
        TI_2 = 0.5*(TI_2[..., 1::2]+TI_2[..., 2::2])

        M0 = source.get_fdata()[...,0]
        # WARNING: the tagged/control alternance is hard-coded.
        delta_M = source.get_fdata()[..., 2::2] - source.get_fdata()[..., 1::2]
        
        with numpy.errstate(divide="ignore", invalid="ignore"):
            # 4D Cerebral Blood Flow in L / kg / s
            CBF = (
              (lambda_ * delta_M)
              / (2*alpha * M0[..., None] * TI_1 * numpy.exp(-TI_2 / T1_a)) 
              * numpy.exp(delta_R2_star * TE))
            
            # Average all volumes
            CBF = numpy.nanmean(CBF, axis=-1)

        # Convert to mL / 100 g / min
        CBF *= 1000 / 10 / (1/60)
        # Clamp to reasonable values
        CBF[numpy.isinf(CBF)] = numpy.nan
        CBF[CBF < -1000] = -1000
        CBF[CBF > +1000] = +1000
        
        nibabel.save(nibabel.Nifti1Image(CBF, source.affine), str(target_path))

def main():
    return entrypoint(
        pASLSiemens, [
            ("source", {"help": "Source ASL image"}),
            ("meta_data", {"nargs": "?", "help": "Source image meta-data"}),
            ("slice_time", {"help": "Slice time image, in the same frame as source"}),
            ("target", {"help": "Target CBF image"})
        ])
