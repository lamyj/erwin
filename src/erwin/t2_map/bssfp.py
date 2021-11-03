import nibabel
import numpy
import spire

from .. import entrypoint, parsing

class bSSFP(spire.TaskFactory):
    """ Compute a map of T2 from bSSFP images.
        
        Reference: "Analytical corrections of banding artifacts in driven
        equilibrium single pulse observation of T2 (DESPOT2)". Jutras et al.
        Magnetic Resonance in Medicine 76(6). 2015.
    """
    
    def __init__(
            self, sources, flip_angles, phase_increments, repetition_time,
            B1_map, T1_map, target):
        """ :param Sequence(str) sources: Paths to source images
            :param Sequence(float) flip_angles: Flip angles (rad)
            :param Sequence(float) phase_increments: Phase increment of the RF \
                pulse in each source image (rad)
            :param float repetition_time,tr: Repetition time (s)
            :param str B1_map,b1_map: Relative B₁ map
            :param str T1_map,t1_map: T₁ map (s)
            :param str target: Path to the target T₂ map (s)
        """
        
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [*sources, B1_map, T1_map]
        self.targets = [target]
        
        self.actions = [
            (
                bSSFP.t2_map, (
                    sources, flip_angles, phase_increments, repetition_time,
                    B1_map, T1_map, target))]
    
    @staticmethod
    def t2_map(
            source_paths, flip_angles, phase_increments, repetition_time, 
            B1_map_path, T1_map_path, T2_map_path):
        
        # Sort images and meta-data according to the pair (ϕ, FA)
        # so that we get (ϕ₁, FA₁), (ϕ₁, FA₂), (ϕ₂, FA₁), (ϕ₂, FA₂), etc.
        order = [
            x[0] for x in sorted(
                zip(range(len(source_paths)), phase_increments, flip_angles),
                key=lambda x: (x[-2], x[-1]))]
        for array in [source_paths, flip_angles, phase_increments]:
            array[:] = [array[x] for x in order]
        
        # Load the images
        sources = [nibabel.load(x) for x in source_paths]
        rB1 = nibabel.load(B1_map_path).get_fdata()
        
        T1 = nibabel.load(T1_map_path).get_fdata()
        T1[T1<0] = 1e-12
        E1 = numpy.exp(-repetition_time/T1)[None, ...]
        
        S = numpy.asarray([source.get_fdata() for source in sources])
        
        alpha = numpy.asarray(flip_angles)[:, None, None, None] * rB1[None, :, :, :]
        
        sin_alpha = numpy.sin(alpha)
        sin_alpha[sin_alpha == 0] = 1e-12
        
        tan_alpha = numpy.tan(alpha)
        tan_alpha[tan_alpha == 0] = 1e-12
        
        # Equation 7, regularized
        numerator = S[0::2]/sin_alpha[0::2] - S[1::2]/sin_alpha[1::2]
        denominator = S[0::2]/tan_alpha[0::2] - S[1::2]/tan_alpha[1::2]
        denominator[denominator == 0] = 1e-12
        m = numerator/denominator
        
        # Equation 4, WARNING complex data possible
        tau_2 = -repetition_time / numpy.log((E1-m) / (1 - m*E1))
        
        # Below equation 11
        K_N = numpy.sqrt(8/(3*len(source_paths)/2))
        
        # Equation 11
        T2_RSS = K_N * numpy.sqrt(numpy.nansum(tau_2**2, axis=0))
        
        nibabel.save(
            nibabel.Nifti1Image(T2_RSS, sources[0].affine),
            T2_map_path)

def main():
    return entrypoint(bSSFP)
