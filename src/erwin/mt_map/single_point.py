import itertools
import multiprocessing
import warnings

import nibabel
import numpy
import scipy.integrate
import scipy.optimize
import spire

from .. import entrypoint, parsing

import pyximport
pyximport.install()
from . import mpf

class SinglePoint(spire.TaskFactory):
    """ Compute the MPF map based on Yarnykh's single point method.
        
        Reference: "Fast macromolecular proton fraction mapping from a single 
        off-resonance magnetization transfer measurement". Yarnykh. Magnetic 
        Resonance in Medicine 68(1). 2012.
    """
    
    def __init__(
            self, MT_off, MT_on, 
            mt_flip_angle, mt_duration, mt_frequency_offset, 
            flip_angle, repetition_time,
            B0_map, B1_map, T1_map, MPF_map):
        spire.TaskFactory.__init__(self, str(MPF_map))
        
        self.B0_map = B0_map
        self.B1_map = B1_map
        self.T1_map = T1_map
        
        self.file_dep = [MT_off, MT_on, B0_map, B1_map, T1_map]
        self.targets = [MPF_map]
        
        self.actions = [
            (
                SinglePoint.mpf_map, 
                (
                    MT_off, MT_on,
                    mt_flip_angle, mt_duration, mt_frequency_offset, 
                    flip_angle, repetition_time, 
                    B0_map, B1_map, T1_map, MPF_map))]
    
    @staticmethod
    def mpf_map(
            MT_off_path, MT_on_path, 
            mt_flip_angle, mt_duration, mt_frequency_offset, 
            flip_angle, repetition_time,
            B0_map_path, B1_map_path, T1_map_path, 
            MPF_map_path):
        
        # Load the images
        MT_off, MT_on = [nibabel.load(x) for x in source_paths]
        B0_map = nibabel.load(B0_map_path)
        B1_map = nibabel.load(B1_map_path)
        T1_map = nibabel.load(T1_map_path)
        
        # Derived data
        T1 = T1_map.get_fdata()
        with numpy.errstate(divide="ignore", invalid="ignore"):
            R1 = 1/T1
        T2_free = 0.022*T1
        delta_omega = mt_frequency_offset - B0_map.get_fdata()
        
        # Compute all possible lineshapes, and get the lineshape for each voxel
        # of the delta_omega map (rounded to the nearest Hz).
        lineshapes = SinglePoint.super_lorentzian_lineshapes(11e-6)
        G = lineshapes[delta_omega.round().astype(int)]
        
        # Saturation power of the MT saturation pulse
        omega_1_rms_nominal = SinglePoint.omega_1_rms_gaussian_pulse(
            mt_duration*1e-3, numpy.radians(mt_flip_angle))
        omega_1_rms = omega_1_rms_nominal * B1_map.get_fdata()
        
        source_arrays = [x.get_fdata() for x in [MT_off, MT_on]]
        if len(meta_data_array[0]["EchoTime"]) > 1:
            source_arrays = [x.mean(axis=-1) for x in source_arrays]
        with numpy.errstate(divide="ignore", invalid="ignore"):
            S_ratio = source_arrays[1]/source_arrays[0]
        
        f0 = 0.10
        
        f = SinglePoint.estimate_f_map(
            S_ratio, R1, T2_free, delta_omega, omega_1_rms, G,
            repetition_time*1e-3, mt_duration*1e-3, 
            numpy.radians(flip_angle), 
            f0)

        # Clamp the MPF map in its "true" range
        f[f<0] = numpy.nan
        f[f>1] = numpy.nan
        
        # Save as percents
        nibabel.save(nibabel.Nifti1Image(1e2*f, MT_off.affine), MPF_map_path)
    
    @staticmethod
    def super_lorentzian_lineshapes(T2_bound):
        """ From "Quantitative Magnetization Transfer Imaging Made Easy with 
            qMTLab: Software for Data Simulation, Analysis, and Visualization".
            Cabana et al. Concepts in Magnetic Resonance 44A(5). 2015
        """
        
        frequency_offsets = numpy.arange(1, 1e4+1)
        G = numpy.zeros(len(frequency_offsets))
        
        # From equation 7. Note that the expression differs from the one given 
        # in doi:10.1006/jmrb.1995.1111 (and also doi:10.1002/mrm.10120 and
        # doi:10.1002/mrm.22562) as the sin θ term disappears.
        for i, offset in enumerate(frequency_offsets):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                integral, _ = scipy.integrate.quad(
                    mpf.super_lorentzian_differential, 0, 1, (offset, T2_bound), 
                    limit=150)
            G[i] = T2_bound * numpy.sqrt(2/numpy.pi) * integral
        
        return G
    
    @staticmethod
    def omega_1_rms_gaussian_pulse(duration, angle):
        """ Estimation of the saturation pulse, w1rms. 
            Fast Macromolecular Proton Fraction Mapping from A Single Off-Resonance 
            Magnetization Transfer Measurement. Yarnykh, 2012 [Eq. 4]"""
        
        def gaussian_pulse(t, tm):
            """ Envelope of a gaussian pulse of duration tm. """
            alpha = 0.5 # for a Hanning window
            Emp = 1 # default value
            
            w = (1-alpha) + alpha*numpy.cos(2*numpy.pi*t/tm)
            b1 = w * (numpy.exp(-numpy.pi*Emp*t))**2 / (4 * numpy.log(2) )
            
            return b1
        
        # Maximum amplitude of a gaussian pulse
        # max_amplitude = -scipy.optimize.minimize_scalar(
        #         lambda t: -gaussian_pulse(t, duration), 
        #         bounds=(0, duration), method='bounded'
        #     ).fun
        
        # Envelope function of the MT pulse
        pulse_envelope = lambda t: gaussian_pulse(t, duration)
        
        # RMS of the pulse
        int_b1_square, _ = scipy.integrate.quad(
            lambda t: pulse_envelope(t)**2, 0, duration, limit=150)
        pulse_rms = numpy.sqrt(int_b1_square/duration)
        # Area of the pulse
        area, _ = scipy.integrate.quad(pulse_envelope, 0, duration, limit=150)
        
        # Saturation power. Note that there is an extra t_m term in eq. 4.
        omega_1_rms = angle * pulse_rms / area
        
        return omega_1_rms
    
    @staticmethod
    def estimate_f_map(
            S_ratio, R1, T2_free, delta_omega, omega_1_rms, 
            G, TR, duration, flip_angle, f0):
        
        shape = S_ratio.shape
        
        chunk_size = int(1e4)
        chunks_count = numpy.cumprod(shape)[-1] // chunk_size
        
        S_ratio = numpy.array_split(S_ratio.ravel(), chunks_count)
        R1 = numpy.array_split(R1.ravel(), chunks_count)
        T2_free = numpy.array_split(T2_free.ravel(), chunks_count)
        delta_omega = numpy.array_split(delta_omega.ravel(), chunks_count)
        omega_1_rms = numpy.array_split(omega_1_rms.ravel(), chunks_count)
        G = numpy.array_split(G.ravel(), chunks_count)
        
        with multiprocessing.Pool(4) as pool:
            f = pool.starmap(
                SinglePoint.estimate_f_map_worker,
                zip(
                    S_ratio, R1, T2_free, delta_omega, omega_1_rms, G,
                    itertools.repeat(TR, len(R1)), 
                    itertools.repeat(duration, len(R1)), 
                    itertools.repeat(flip_angle, len(R1)), 
                    itertools.repeat(f0, len(R1))))
        
        f = numpy.concatenate(f).reshape(shape)
        return f
    
    @staticmethod
    def estimate_f_map_worker(
            S_ratio, R1, T2_free, delta_omega, omega_1_rms, 
            G, TR, duration, flip_angle, f0):
        
        f = numpy.empty(R1.shape)
        for index in numpy.ndindex(f.shape):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                root = scipy.optimize.fsolve(
                    mpf.model, f0, 
                    (
                        S_ratio[index], R1[index], T2_free[index], 
                        delta_omega[index], omega_1_rms[index], G[index], 
                        TR, duration, flip_angle))
            f[index] = root[0]
        
        return f

def main():
    return entrypoint(
        SinglePoint, [
            ("--MT-off", "--mt-off", {"help": "SPGR image without MT pulse"}),
            ("--MT-on", "--mt-on", {"help": "SPGR image with MT pulse"}),
            (
                "--mt-flip-angle", {
                    "type": float, "help": "Flip angle of the MT pulse (°)"}),
            (
                "--mt-duration", {
                    "type": float, "help": "Duration of the MT pulse (ms)"}),
            (
                "--mt-frequency-offset", {
                    "type": float,
                    "help": "Frequency offset of the MT pulse (Hz)"}),
            parsing.FlipAngle,
            parsing.RepetitionTime,
            ("--B0-map", "--b0-map", {"help": "B0 map in SPGR space"}),
            ("--B1-map", "--b1-map", {"help": "B1 map in SPGR space"}),
            ("--T1-map", "--t1-map", {"help": "T1 map in SPGR space"}),
            ("--MPF-map", "--mpf-map", {"help": "Path to the target MPF map"})])
