import cython
from libc.math cimport fabs, cos, exp, log, pi, sin

def int_superLorentzian(float u, float Delta, float T2b):
    return 1. / fabs(3*u**2 - 1) * exp( -2 * ( (2*pi*Delta*T2b) / (3*u**2 -1) )**2 )

@cython.cdivision(True)
cdef newRamani_corr(
        float f, float R1, float T2f, float tm, float Delta, float TR, 
        float FA, float w1rms, float G):
    """ Computation of the signal proportional to the magnetization, using 
        Ramani formula. """
    
    cdef float R1f = R1
    cdef float R1b = R1
    
    cdef float R = 19. # [s^-1] 
    cdef float k = R*f/(1.-f)
    
    cdef float Wf = ( w1rms / (2*pi*Delta) )**2 / T2f
        
    cdef float Wb = pi * w1rms**2 * G
    
    cdef float beta = -log(cos(FA))/TR
    cdef float s = tm/TR
    
    cdef float F = f/(1.-f)
    cdef float Y1 = R1b*k/R1f + s*Wb + R1b + k/F
    cdef float Y2 = k/R1f*(R1b + s*Wb) + (1. + s*Wf/R1f + beta/R1f)*(s*Wb + R1b + k/F)
    
    cdef float Mzf = (1.-f)*Y1/Y2
    
    cdef float S = Mzf * sin(FA)
    
    return S

@cython.cdivision(True)
def model(
        float f, float R1, float T2f, float tm, float Delta, TR, FA, 
        float w1rms, float G, float S_ratio):
    """ Definition of the model, using the ratio of intensity signals, the
        estimated value of the signal with magnetization transfer and the one
        without magnetization transfer. """
    
    Smt = newRamani_corr(f, R1, T2f, tm, Delta, TR[0], FA[0], w1rms, G)
    Sref = newRamani_corr(f, R1, T2f, tm, Delta, TR[1], FA[1], 0, G)

    return float('nan') if Sref == 0 else S_ratio - Smt / Sref
