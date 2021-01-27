import json
import re

import nibabel
import numpy
import scipy
import spire

from .. import entrypoint

class UnwrapPhase(spire.TaskFactory):
    """ Unwrap the phase image.
        
        Reference: Fast phase unwrapping algorithm for interferometric 
        applications. Schoffield and Zhu. Optics Letters 28(14). 2003.
    """
    
    def __init__(self, source, target, meta_data=None, padding=24):
        spire.TaskFactory.__init__(self, target)
        
        self.sources = [source]
        
        if meta_data is None:
            meta_data = re.sub(r"\.nii(\.gz)?$", ".json", str(source))
        
        self.file_dep = [source, meta_data]
        self.targets = [target]
        
        self.actions = [
            (UnwrapPhase.unwrap_phase, (source, meta_data, padding, target))]
    
    @staticmethod
    def unwrap_phase(source_path, meta_data_path, padding, target_path):
        try:
            with open(meta_data_path) as fd:
                meta_data = json.load(fd)
        except FileNotFoundError:
            meta_data = None
        
        phi_w_image = nibabel.load(source_path)
        phi_w = phi_w_image.get_fdata()
        
        # Siemens phase images are mapping [-π, +π[ to [-4096, +4094]
        if (
                meta_data is not None
                and meta_data["ImageType"][2] == "P" 
                and meta_data["Manufacturer"][0] == "SIEMENS"):
            phi_w *= numpy.pi / 4096
        
        # scipy.fft has a parallel version while numpy.fft does not.
        fft = lambda x: scipy.fft.fftn(x, workers=4)
        ifft = lambda x: scipy.fft.ifftn(x, workers=4)
        
        # Pad on all spatial dimensions
        phi_w = numpy.pad(phi_w, 3*[2*[padding]]+[[0,0]], mode="constant")
        
        # Compute the k-space coordinates and their norm
        k = numpy.array(
            numpy.meshgrid(
                *[
                    numpy.fft.fftfreq(n, d) 
                    for n,d in zip(
                        phi_w.shape[:3], phi_w_image.header["pixdim"][1:4])],
                indexing="ij"
            ))
        norm = numpy.sum(k**2, axis=0)
        
        # Process volume by volume as we need to allocate large complex-double
        # arrays for the FFT
        phi_prime = numpy.empty(phi_w_image.shape, float)
        for i in range(phi_w.shape[3]):
            cos_phi_w = numpy.cos(phi_w[..., i])
            sin_phi_w = numpy.sin(phi_w[..., i])
            laplacian = (
                cos_phi_w * ifft(norm * fft(sin_phi_w))
                - sin_phi_w * ifft(norm * fft(cos_phi_w)))

            # Avoid division by 0. This also centers the mean phase of the
            # image.
            old = norm[0,0,0]
            norm[0,0,0] = 1
            phi_volume = fft(laplacian)
            phi_volume /= norm
            phi_volume[0,0,0] = 0
            norm[0,0,0] = old

            phi_volume = ifft(phi_volume)

            cropped = tuple(3*[slice(padding, -padding)])
            phi_prime[..., i] = phi_volume[cropped].real
        
        nibabel.save(
            nibabel.Nifti1Image(phi_prime, phi_w_image.affine), target_path)

def main():
    return entrypoint(
        UnwrapPhase, [
            ("source", {"help": "Wrapped phase image"}),
            ("target", {"help": "Unwrapped phase image"}),
            (
                "--padding",
                {"help": "Padding size", "type":int, "default": 24})])
