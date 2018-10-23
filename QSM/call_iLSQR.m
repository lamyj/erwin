function call_iLSQR(tissuephase_filename, mask_filename, H_x, H_y, H_z, TE, ...
                    B0, voxelsize_x, voxelsize_y, voxelsize_z, niter, ...
                    tol_step1, tol_step2, Kthreshold, ...
                    padsize_x, padsize_y, padsize_z, ofilename)

    addpath('/base_image/schizo/connectsz/scripts/matlab/FINAL/TOOLS/STI_Suite_v2.2/Core_Functions')
  
    hdr = spm_vol(tissuephase_filename);
    tissuephase_data = spm_read_vols(hdr);
    mask_data = spm_read_vols(spm_vol(mask_filename));
        
    params.H = [str2double(H_x) str2double(H_y) str2double(H_z)];
    params.TE = str2double(TE);
    params.B0 = str2double(B0);
    params.voxelsize = [str2double(voxelsize_x) str2double(voxelsize_y) str2double(voxelsize_z)];
    params.niter = str2double(niter);
    params.tol_step1 = str2double(tol_step1);
    params.tol_step2 = str2double(tol_step2);
    params.Kthreshold = str2double(Kthreshold);
    params.padsize = [str2double(padsize_x) str2double(padsize_y) str2double(padsize_z)];
    
    [Susceptibility] = QSM_iLSQR(tissuephase_data, mask_data, 'params', params);

    hdr.descrip = ['Susceptibility']; 
    hdr.fname = ofilename;
    hdr.dt = [4 0];  % assume int16 and a specific byte ordering
    hdr.pinfo = [1e-2 0 0]';
    spm_write_vol(hdr, 1e3*Susceptibility);
          
end