import nibabel
import numpy
import spire
import sycomore
from sycomore.units import *

from .. import entrypoint, parsing

class VFA(spire.TaskFactory):
    """ Compute the T1 map based on SPGR images acquired with a VFA scheme.
        
        Reference: T1 Mapping Using Spoiled FLASH-EPI Hybrid Sequences and 
        Varying Flip Angles. Preibisch & Deichmann. Magnetic Resonance in 
        Medicine 61(1). 2009.
    """
    
    def __init__(
            self, sources, flip_angles, echo_time, repetition_time, B1_map,
            target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [*sources, B1_map]
        self.targets = [target]
        
        self.actions = [
            (VFA.t1_map, (
                sources, flip_angles, echo_time, repetition_time, B1_map,
                target))]
    
    def t1_map(
            source_paths, flip_angles, echo_time, repetition_time, B1_map_path,
            T1_map_path):
        """T1 map generation"""
        
        # Load the VFA signal
        sources = [nibabel.load(x) for x in source_paths]
        signal = numpy.asarray([x.get_fdata() for x in sources])
        
        # Compute a flip angle map from the nominal flip angles
        B1_map = nibabel.load(B1_map_path).get_fdata()
        flip_angle_map = numpy.asarray([B1_map * x for x in flip_angles])
        
        # Compute the B1-corrected T1 map
        with numpy.errstate(divide="ignore", invalid="ignore"):
            X = signal / numpy.tan(flip_angle_map)
            Y = signal / numpy.sin(flip_angle_map)
            # Eq. 3b
            SL = (Y[0]-Y[1]) / (X[0]-X[1])
            # Eq. 3a. The flip angles have been corrected by the B1 map, but T1'
            # still includes the effects of the RF spoiling
            T1_prime = -repetition_time / numpy.log(SL)
        
        # Compute the RF-spoiling correction
        pA, pB = VFA.rf_spoiling_correction_paremeters(
            [x*rad for x in flip_angles], echo_time*s, repetition_time*s)
        
        A = numpy.polyval(pA, B1_map)
        B = numpy.polyval(pB, B1_map)
        T1 = A + B*T1_prime
        
        T1[T1<0] = numpy.nan
        T1[T1>10] = numpy.nan
        nibabel.save(nibabel.Nifti1Image(T1, sources[0].affine), T1_map_path)
    
    @staticmethod
    def rf_spoiling_correction_paremeters(flip_angles, TE, TR):
        """ Compute the RF-spoiling correction based on "Influence of RF 
            Spoiling on the Stability and Accuracy of T1 Mapping Based on 
            Spoiled FLASH With Varying Flip Angles". Preibisch and Deichmann.
            Magnetic Resonance in Medicine 61(1). 2009.
        """
        
        phase_step_increment = 50*deg
        
        C_RF_range = numpy.arange(0.7, 1.3, 0.1)
        
        T1_range = sycomore.linspace(0.6*s, 1.8*s, 20)
        T2 = 80*ms
        
        A = numpy.zeros(len(C_RF_range))
        B = numpy.zeros(len(C_RF_range))
        
        for k, C_RF in enumerate(C_RF_range):
            
            T1_app = numpy.zeros(len(T1_range))
            
            for i, T1 in enumerate(T1_range):
                # Simulate the signals for all the flip angles.
                signals = numpy.asarray([
                    VFA.simulate_spgr(
                        T1, T2, flip_angle*C_RF, phase_step_increment, TE, TR)
                    for flip_angle in flip_angles])
                
                # Linear fit of S/α = A + B S⋅α (eq. 3)
                X = numpy.zeros((len(flip_angles), 2))
                X[:,0] = 1
                X[:,1] = signals*[x.magnitude for x in flip_angles]
                
                Y = signals/[x.magnitude for x in flip_angles]
                
                intercept, slope = numpy.linalg.lstsq(X, Y, rcond=None)[0]
                # Intercept is ρ, slope is -T1'/(2TR). Since T1' = T1⋅C_RF²,
                # the slope is can be written as -T1⋅C_RF² / 2TR and thus
                T1_app[i] = -slope * 2*TR.magnitude / C_RF**2
            
            X = numpy.zeros((len(T1_app), 2))
            X[:,0] = 1
            # FIXME? shouldn't this be T1_apparent[:,k]
            X[:,1] = T1_app
            Y = numpy.asarray([x.magnitude for x in T1_range]).reshape((-1, 1))
            intercept, slope = numpy.linalg.lstsq(X, Y, rcond=None)[0]
            A[k] = intercept
            B[k] = slope
        
        pA = numpy.polyfit(C_RF_range, A, 2)
        pB = numpy.polyfit(C_RF_range, B, 2)
        return pA, pB
    
    @staticmethod
    def simulate_spgr(T1, T2, flip_angle, phase_step_increment, TE, TR):
        """ EPG simulation of the SPGR sequence.
        """
        
        # We just need a non-null value
        slice_thickness = 5*mm
        G_readout = (2*numpy.pi*rad / (sycomore.gamma*slice_thickness))/(TR-TE)
        species = sycomore.Species(T1, T2)
        model = sycomore.epg.Discrete(species)
        echo = None
        for repetition in range(500):
            phase = phase_step_increment * repetition * (repetition+1)/2
            model.apply_pulse(flip_angle, phase)
            
            model.apply_time_interval(TE)
            echo = model.echo * numpy.exp(-1j*phase.convert_to(rad))
            
            model.apply_time_interval(TR-TE, G_readout)
        return numpy.abs(echo)

def main():
    return entrypoint(
        VFA, [
            parsing.Multiple(
                [
                    "--sources",
                    {"help": "SPGR images with different flip angles"}],
                2),
            parsing.Multiple(parsing.FlipAngles, 2),
            parsing.EchoTime,
            parsing.RepetitionTime,
            ("--B1-map", "--b1-map", {"help": "B1 map in SPGR space"}),
            ("--target", {"help": "Path to the target T1 map"})])
