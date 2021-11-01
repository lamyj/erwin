import nibabel
import numpy
import spire

from .. import entrypoint, parsing

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
            self, sources, flip_angle, phase_increments, repetition_time,
            B1_map, T1_map, target):
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

        alpha = numpy.radians(flip_angle)
        alpha *= B1
        
        TR = repetition_time*1e-3
        
        if not isinstance(T1, float):
            T1 = nibabel.load(T1).get_fdata()

        phi = numpy.radians(phase_increments)

        S = [x.get_fdata() for x in sources]
        S_sq = numpy.power(S, 2)

        eta = 0.5*(1+numpy.cos(alpha))/(1-numpy.cos(alpha))
        xi = pSSFP.compute_xi(eta)
        
        T2_biased = (
            2*TR/xi * numpy.sqrt(
                (S_sq[0]-S_sq[1]) 
                / (S_sq[1]*phi[1]**2 - S_sq[0]*phi[0]**2)))
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
        pSSFP, [
            (
                "--sources", {
                    "nargs": "+", "metavar": "source",
                    "help": "pSSFP images with different phase steps increments"}),
            parsing.FlipAngle,
            parsing.RepetitionTime,
            parsing.Multiple(
                [
                    "--phase-increments", {
                        "type": float,
                        "help": "Phase increment for each bSSFP image (°)"}],
                2),
            ("--B1-map", "--b1-map", {"help": "B1 map in bSSFP space"}),
            ("--T1-map", "--t1-map", {"help": "T1 map in bSSFP space"}),
            ("--target", {"help": "Target T2 map"})])
