#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define np 500 /* number of RF pulses */
#define M_PI 3.1416

double epg(double FA, double phi_inc, double TR, double T1, double T2)
{
    int i, j, n, m;
    double fx[2*np],fy[2*np],zx[np],zy[np];

    /* pre pulse configurations */
    double pfx[2*np],pfy[2*np],pzx[np],pzy[np];
    
    /* post pulse configurations */
    double a,b,c,d,e,f,g,h,hb,gb,ec,fc;
    double phi,alpha,e1,e2;
    
    /* set relaxation parameters */
    e1 = exp(-TR/T1);
    e2 = exp(-TR/T2);
    
    for (i=0;i<2*np;i++) /* initialize all states */
    {
        fx[i] = 0.0; if (i<np) zx[i] = 0.0;
        fy[i] = 0.0; if (i<np) zy[i] = 0.0;
    }
    zx[0] = 1.0;
    /* equilibrium magnetization M0=1 */
    
    alpha = FA*M_PI/180.0;
    
    /* outer pulse loop */
    for (j=0;j<np-1;j++)
    {
        /* setting of RF parameters and matrix coefficients */
    
        phi = phi_inc*M_PI/180.0*j*(j+1)/2; /* quadratic variation of RF phase*/
    
        a = cos(alpha/2); a *= a;
        /* set coefficients of transition matrix */
        b = sin(alpha/2); b *= b;
        c = sin(alpha);
        d = cos(alpha);
        e = sin(phi);
        f = cos(phi);
        g = sin(2.0*phi);
        h = cos(2.0*phi);
        hb = h*b; gb = g*b; ec = e*c; fc = f*c;
    
        for (i=0;i<j+1;i++)
        /* application of RF rotation
        matrix on all states */
        {
            n = np + i; m = np - i;
            pfx[n] = a*fx[n] + hb*fx[m] + gb*fy[m] + ec*zx[i] + fc*zy[i];
            pfy[n] = a*fy[n] - hb*fy[m] + gb*fx[m] - fc*zx[i] + ec*zy[i];
            pfx[m] = hb*fx[n] + gb*fy[n] + a*fx[m] + ec*zx[i] - fc*zy[i];
            pfy[m] = gb*fx[n] - hb*fy[n] + a*fy[m] - fc*zx[i] - ec*zy[i];
            pzx[i] = (-ec*fx[n] + fc*fy[n] - ec*fx[m] + fc*fy[m] + 2.0*d*zx[i])/2.0;
            pzy[i] = (-fc*fx[n] - ec*fy[n] + fc*fx[m] + ec*fy[m] + 2.0*d*zy[i])/2.0;
        }
    
        for (i=-j;i<j+1;i++)
        /* time evolution and relaxation of all states */
        {
            n = np + i;
            fx[n+1] = pfx[n]*e2;
            fy[n+1] = pfy[n]*e2;
            if (i>0) zx[i] = pzx[i]*e1;
            if (i==0) zx[i] = pzx[i]*e1 + 1.0 - e1;
            if (i>=0) zy[i] = pzy[i]*e1;
        }
    }
    double Mt = sqrt(pfx[np]*pfx[np] + pfy[np]*pfy[np]);
    return Mt;
}
    

int main (int argc, char *argv[])
{
    
    double FA, phi_inc, TR, T1, T2, Mt;
     
    if (argc == 6)
    {
        FA = atof(argv[1]);
        phi_inc = atof(argv[2]);
        TR = atof(argv[3]);
        T1 = atof(argv[4]);
        T2 = atof(argv[5]);
        Mt = epg(FA, phi_inc, TR, T1, T2);
        printf("%f", Mt);
        exit(EXIT_SUCCESS);
    }
    else
    {
        printf("ERROR: Wrong number of inputs.\n");
        exit(EXIT_FAILURE);
    }
}