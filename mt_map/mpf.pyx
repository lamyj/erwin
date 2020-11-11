import cython
from libc.math cimport fabs, cos, exp, log, pi, sin

@cython.cdivision(True)
def super_lorentzian_differential(float u, float Delta, float T2b):
    return 1. / fabs(3*u**2 - 1) * exp(-2 * ((2*pi*Delta*T2b) / (3*u**2 - 1))**2)

@cython.cdivision(True)
cdef newRamani_corr(
        float f, float R1, float T2_free, float duration, float delta_omega, 
        float TR, float flip_angle, float omega_1_rms, float G):
    """ Computation of the signal proportional to the magnetization, using 
        Ramani formula. """
    
    cdef float R1f = R1
    cdef float R1b = R1
    
    cdef float R = 19. # [s^-1] 
    cdef float k = R*f/(1.-f)
    
    # Time-averaged saturation rate for the free and bound pools
    cdef float Wf = ( omega_1_rms / (2*pi*delta_omega) )**2 / T2_free
    cdef float Wb = pi * omega_1_rms**2 * G
    
    cdef float beta = -log(cos(flip_angle))/TR
    cdef float s = duration/TR
    
    cdef float F = f/(1.-f)
    cdef float Y1 = R1b*k/R1f + s*Wb + R1b + k/F
    cdef float Y2 = k/R1f*(R1b + s*Wb) + (1. + s*Wf/R1f + beta/R1f)*(s*Wb + R1b + k/F)
    
    cdef float Mzf = (1.-f)*Y1/Y2
    
    cdef float S = Mzf * sin(flip_angle)
    
    return S

@cython.cdivision(True)
def model(
        float f, 
        float S_ratio, float R1, float T2_free, float delta_omega, 
        float omega_1_rms, float G, 
        float TR, float duration, float flip_angle):
    
    S_ref = newRamani_corr(
        f, R1, T2_free, duration, delta_omega, TR, flip_angle, 0, G)
    S_mt = newRamani_corr(
        f, R1, T2_free, duration, delta_omega, TR, flip_angle, omega_1_rms, G)
    
    return float("nan") if S_ref == 0 else S_ratio - S_mt / S_ref
