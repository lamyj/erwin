import argparse
import itertools
import json
import multiprocessing
import re
import sys
import warnings

import nibabel
import numpy
import scipy.integrate
import scipy.optimize
import spire

from . import common

import pyximport
pyximport.install()
from . import mpf

class SinglePoint(spire.TaskFactory):
    """ Compute the MPF map based on Yarnykh's single point method.
        
        Reference: "Fast macromolecular proton fraction mapping from a single 
        off-resonance magnetization transfer measurement". Yarnykh. Magnetic 
        Resonance in Medicine 68(1). 2012.
    """
    
    def __init__(self, sources, B0_map, B1_map, T1_map, MPF_map, meta_data=None):
        spire.TaskFactory.__init__(self, MPF_map)
        
        self.sources = sources
        
        if meta_data is None:
            meta_data = [
                re.sub(r"\.nii(\.gz)?$", ".json", str(x)) for x in sources]
        self.meta_data = meta_data
        
        self.B0_map = B0_map
        self.B1_map = B1_map
        self.T1_map = T1_map
        
        self.file_dep = list(itertools.chain(
            sources, meta_data, [B0_map, B1_map, T1_map]))
        self.targets = [MPF_map]
        
        self.actions = [
            (
                SinglePoint.mpf_map, 
                (sources, meta_data, B0_map, B1_map, T1_map, MPF_map))]
    
    @staticmethod
    def mpf_map(
            source_paths, meta_data_paths, 
            B0_map_path, B1_map_path, T1_map_path, 
            MPF_map_path):
        
        # Load the meta-data
        meta_data_array = []
        for path in meta_data_paths:
            with open(path) as fd:
                meta_data_array.append(json.load(fd))
        
        # Get the pulse data
        pulses = [common.get_pulses(x) for x in meta_data_array]
        mt_pulses_info = [common.get_mt_pulse_info(x) for x in meta_data_array]
        
        # Sort the source paths, meta data and pulse info 
        # in (MT_off, MT_on) order
        source_paths = [
            path for path, _ in sorted(
                zip(source_paths, pulses), key=lambda x: len(x[1]))]
        meta_data_array = [
            meta_data for meta_data, _ in sorted(
                zip(meta_data_array, pulses), key=lambda x: len(x[1]))]
        pulses.sort(key=lambda x: len(x))
        mt_pulses_info = [
            mt_pulse_info for mt_pulse_info, _ in sorted(
                zip(mt_pulses_info, pulses), key=lambda x: len(x[1]))]
        
        # Load the images
        sources = [nibabel.load(x) for x in source_paths]
        B0_map = nibabel.load(B0_map_path)
        B1_map = nibabel.load(B1_map_path)
        T1_map = nibabel.load(T1_map_path)
        
        # Derived data
        T1 = T1_map.get_fdata()
        with numpy.errstate(divide="ignore", invalid="ignore"):
            R1 = 1/T1
        T2_free = 0.022*T1
        delta_omega = mt_pulses_info[1]["frequency_offset"] - B0_map.get_fdata()
        
        # Compute all possible lineshapes, and get the lineshape for each voxel
        # of the delta_omega map (rounded to the nearest Hz).
        lineshapes = SinglePoint.super_lorentzian_lineshapes(11e-6)
        G = lineshapes[delta_omega.round().astype(int)]
        
        # Saturation power of the MT saturation pulse
        omega_1_rms_nominal = SinglePoint.omega_1_rms_gaussian_pulse(
            mt_pulses_info[1]["duration"], mt_pulses_info[1]["angle"])
        omega_1_rms = omega_1_rms_nominal * B1_map.get_fdata()
        
        source_arrays = [x.get_fdata() for x in sources]
        if len(meta_data_array[0]["EchoTime"]) > 1:
            source_arrays = [x.mean(axis=-1) for x in source_arrays]
        with numpy.errstate(divide="ignore", invalid="ignore"):
            S_ratio = source_arrays[1]/source_arrays[0]
        
        f0 = 0.10
        
        f = SinglePoint.estimate_f_map(
            S_ratio, R1, T2_free, delta_omega, omega_1_rms, G,
            meta_data_array[0]["RepetitionTime"][0]*1e-3, 
            mt_pulses_info[1]["duration"], 
            numpy.radians(meta_data_array[0]["FlipAngle"][0]), 
            f0)

        # Clamp the MPF map in its "true" range
        f[f<0] = numpy.nan
        f[f>1] = numpy.nan
        
        # Save as percents
        nibabel.save(nibabel.Nifti1Image(1e2*f, sources[0].affine), MPF_map_path)
    
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
    parser = argparse.ArgumentParser(description=SinglePoint.__doc__)
    parser.add_argument(
        "sources", nargs=2, help="SPGR images with different flip angles")
    parser.add_argument("B0_map", help="B0 map in SPGR space")
    parser.add_argument("B1_map", help="B1 map in SPGR space")
    parser.add_argument("T1_map", help="T1 map in SPGR space")
    parser.add_argument("MPF_map", help="Path to the target MPF map")
    arguments = parser.parse_args()
    
    task = SinglePoint(**vars(arguments))
    SinglePoint.mpf_map(
        task.sources, task.meta_data, task.B0_map, task.B1_map, task.T1_map,
        *task.targets)
