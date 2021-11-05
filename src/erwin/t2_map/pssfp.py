import nibabel
import numpy
import spire

from .. import entrypoint
from ..cli import *

class pSSFP(spire.TaskFactory):
    """ Compute a map of T2 from pSSFP images.
        
        References:
        
        - Factors controlling T2 mapping from partially spoiled SSFP sequence: 
          Optimization for skeletal muscle characterization. L. de Sousa et al.
          Magnetic Resonance in Medicine 67(5). 2012.
        - Steady state of gradient echo sequences with radiofrequency phase 
          cycling: Analytical solution, contrast enhancement with partial
          spoiling. Ganter. Magnetic Resonance in Medicine 55(1). 2006.
    """
    
    def __init__(
            self, sources: Tuple[str, ...], flip_angle: float,
            phase_increments: Tuple[float, ...], repetition_time: float,
            B1_map: str, T1_map: str, target: str):
        """ :param sources: Paths to source images
            :param flip_angle: Flip angle (rad)
            :param phase_increments: Phase increment of the RF pulse in each source image (rad)
            :param repetition_time: Repetition time (s)
            :param B1_map: Relative B₁ map
            :param T1_map: T₁ map or global T1 value (s)
            :param target: Path to the target T₂ map (s)
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        try:
            global_T1 = float(T1_map)
        except ValueError:
            global_T1 = None
        
        self.file_dep = [*sources, B1_map]
        if not global_T1:
            self.file_dep.append(T1_map)
        self.targets = [target]
        
        self.actions = [
            (
                pSSFP.t2_map, (
                    sources, flip_angle, phase_increments, repetition_time,
                    B1_map, global_T1 if global_T1 else T1_map, target))]
    
    @staticmethod
    def t2_map(
            source_paths, flip_angle, phase_increments, repetition_time,
            B1_map_path, T1, T2_map_path):

        sources = [nibabel.load(x) for x in source_paths]
        B1 = nibabel.load(B1_map_path).get_fdata()

        alpha = flip_angle*B1
        
        if not isinstance(T1, float):
            T1 = nibabel.load(T1).get_fdata()

        S = [x.get_fdata() for x in sources]
        S_sq = numpy.power(S, 2)

        eta = 0.5*(1+numpy.cos(alpha))/(1-numpy.cos(alpha))
        xi = pSSFP.compute_xi(eta)
        
        T2_biased = (
            2*repetition_time/xi * numpy.sqrt(
                (S_sq[0]-S_sq[1]) 
                / (S_sq[1]*phase_increments[1]**2 - S_sq[0]*phase_increments[0]**2)))
        T2 = T2_biased / (1 - 3/2*(eta * T2_biased / T1))

        nibabel.save(nibabel.Nifti1Image(T2, sources[0].affine), T2_map_path)

    @staticmethod
    def compute_xi(eta, N=20):
        """ Compute the ξ factor of Ganter's paper (Eq. 34) given η and the 
            order of the continued fraction.
            
            The default order of the continued fraction (N=20) yields less than 
            1% difference with a very high-order evaluation (N=1_000_000) for 
            all flip angles larger than 5°. 
            
            Note that the values given in table 1 of Ganter's paper are those
            for ξ₀/180*π if we follow the definition of Eq. 34. This correction
            factor is due to the that the phase step increment ϕ is expressed
            in degrees. This function returns the _uncorrected_ value.
        """
        
        xi = (2*(N+1) + 1)*(eta + 1)
        for k in range(N, -1, -1):
            xi = (2*k + 1)*(eta + 1) - (eta * (k+1))**2 / xi
        return xi

def main():
    return entrypoint(
        pSSFP, {
            "repetition_time": "tr", "B1_map": "b1_map", "T1_map": "t1_map"})
