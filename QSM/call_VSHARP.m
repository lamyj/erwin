function call_MRPhaseUnwrapVSHARP(unwrappedphase_filename, mask_filename, voxelsize_x, voxelsize_y, voxelsize_z, ofilename)
    
    addpath('/base_image/schizo/connectsz/scripts/matlab/FINAL/TOOLS/STI_Suite_v2.2/Core_Functions')
    
    hdr = spm_vol(mask_filename);
    mask_data = spm_read_vols(hdr);
    phi = spm_read_vols(spm_vol(unwrappedphase_filename));
    
    voxelsize = [str2double(voxelsize_x) str2double(voxelsize_y) str2double(voxelsize_z)];    
    Unwrapped_Phase = sum(phi,4);

    [TissuePhase,~] = V_SHARP(Unwrapped_Phase, mask_data, 'voxelsize', voxelsize);
    TissuePhase = single(TissuePhase);
    
    ohdr = hdr;
    ohdr.descrip = ['Tissue Phase']; 
    ohdr.fname = ofilename;
    ohdr.dt = [4 0];  % assume int16 and a specific byte ordering
    ohdr.pinfo = [1e-3 0 0]';
    spm_write_vol(ohdr, TissuePhase);
            
end