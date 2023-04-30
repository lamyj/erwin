import nibabel
import numpy
import spire

from .. import entrypoint, get_path, load
from ..cli import *

class DoubleEcho(spire.TaskFactory):
    """ ΔB₀ map (in Hz) using the phase difference between two echoes.
        
        Reference: "An in vivo automated shimming method taking into account
        shim current constraints". Wen & Jaffer. Magnetic Resonance in Medicine
        34(6), pp. 898-904. 1995. doi:10.1002/mrm.1910340616
    """
    
    def __init__(self, 
            magnitude: Tuple[str,str], phase: Tuple[str,str],
            echo_times: Tuple[float,float], target: str):
        """ :param magnitude: Path to magnitude images
            :param phase: Path to phase images
            :param echo_times: Echo times (s)
            :param target: Path to target ΔB₀ map (Hz)
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [get_path(x) for x in [*magnitude, *phase]]
        self.targets = [target]
        
        self.actions = [
            (DoubleEcho.b0_map, (magnitude, phase, echo_times, target))]
    
    @staticmethod
    def b0_map(magnitude_paths, phase_paths, echo_times, B0_map_path):
        magnitude = [load(x) for x in magnitude_paths]
        phase = [load(x) for x in phase_paths]
        
        # Complex signal for the two echoes
        S = [
            m.get_fdata() * numpy.exp(1j*p.get_fdata())
            for m,p in zip(magnitude, phase)]
        
        # Un-normalized, complex, phase difference
        delta_phase = S[1] * S[0].conj()
        # Real phase difference
        delta_phase = numpy.angle(delta_phase)
        
        # Difference between echo times in seconds.
        delta_TE = (echo_times[1] - echo_times[0])
        
        # ΔB₀ map in Hz
        B0_map = delta_phase / (2*numpy.pi*delta_TE)
        
        nibabel.save(
            nibabel.Nifti1Image(B0_map, magnitude[0].affine), B0_map_path)

def main():
    return entrypoint(DoubleEcho, {"echo_times": "te"})
