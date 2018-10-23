#!/bin/bash

if [[ "$1" == "-h" ]]; then
    printf "Bash script interface for calling STI_Suite script for QSM estimation.\n"
    printf "Usage: call_matlab MRPhaseUnwrapVSHARP [phase data filename] [brain mask filename] [voxelsize_x] [voxelsize_y] [voxelsize_z] [padsize_x] [padsize_y] [padsize_z] [output filename]\n"
    printf "Usage: call_matlab VSHARP [unwrapped phase data filename] [brain mask filename] [voxelsize_x] [voxelsize_y] [voxelsize_z] [output filename]\n"
    printf "Usage: call_matlab iLSQR [tissue phase filename] [brain mask filename] [H_x] [H_y] [H_z] [TE] [B0] [voxelsize_x] [voxelsize_y] [voxelsize_z] [niter] [tol_step1] [tol_step2] [Kthreshold] [padsize_x] [padsize_y] [padsize_z] [ofilename]\n"
    
else
    MATLAB_SCRIPT=$(pwd)"/"$1".m"
    
    if [[ ! -f $MATLAB_SCRIPT ]]; then
        echo "Script $MATLAB_SCRIPT not found."
    
    else
        echo $1
    
        if [[ "$1" == "call_MRPhaseUnwrapVSHARP" ]]; then
            matlab -nojvm -r "$1 $2 $3 $4 $5 $6 $7 $8 $9 ${10}; exit"

        elif [[ "$1" == "call_iLSQR" ]]; then             
            matlab -nojvm -r "$1 $2 $3 $4 $5 $6 $7 $8 $9 ${10} ${11} ${12} ${13} ${14} ${15} ${16} ${17} ${18} ${19}; exit"
            
        elif [[ "$1" == "call_VSHARP" ]]; then
            matlab -nojvm -r "$1 $2 $3 $4 $5 $6 $7; exit"
    
        fi
    
    fi

fi