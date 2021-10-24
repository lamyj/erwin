import pathlib
import subprocess

import nibabel
import numpy
import spire

from .. import entrypoint

class ApplyAnts(spire.TaskFactory):
    """ Apply a 4D motion-correction estimated by ANTs to a time series.
    """
    
    def __init__(self, time_series, transforms, reference, target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [time_series, transforms, reference]
        self.targets = [target]
        self.actions = [
            (
                ApplyAnts.apply_transform, 
                (time_series, transforms, reference, pathlib.Path(target)))]
    
    def apply_transform(
            time_series_path, transforms_path, reference_path, target_path):
        # Save first volume of reference image only once since the affine matrix
        # is the same for all reference volumes.
        reference = nibabel.load(reference_path)
        reference_temp = (
            target_path.parent/"__{}_reference.nii".format(target_path.name))
        nibabel.save(
            nibabel.Nifti1Image(reference.get_fdata()[...,0], reference.affine), 
            reference_temp)
        
        # Load the transforms, re-arrange so that the volumes are on the first
        # axis.
        transforms = nibabel.load(transforms_path)
        transforms_array = numpy.transpose(
            transforms.get_fdata(), [3, 0, 1, 2, 4])
        
        # Load the transforms, re-arrange so that the volumes are on the first
        # axis.
        time_series = nibabel.load(time_series_path)
        time_series_array = numpy.transpose(
            time_series.get_fdata(), [3, 0, 1, 2])
        
        transform_temp = (
            target_path.parent/"__{}_transform.nii".format(target_path.name))
        temp = (
            target_path.parent/"__{}_temp.nii".format(target_path.name))
        for transform, volume in zip(transforms_array, time_series_array):
            nibabel.save(
                nibabel.Nifti1Image(transform, transforms.affine), 
                transform_temp)
            nibabel.save(nibabel.Nifti1Image(volume, time_series.affine), temp)
            
            subprocess.check_call([
                "antsApplyTransforms",
                "-i", temp, "-r", reference_temp, "-t", transform_temp,
                "-o", temp])
            
            volume[:] = nibabel.load(temp).get_fdata()
        
        # Re-arrange time series array in original order
        time_series_array = numpy.transpose(time_series_array, [1, 2, 3, 0])
        nibabel.save(
            nibabel.Nifti1Image(time_series_array, reference.affine), 
            target_path)

def main():
    return entrypoint(
        ApplyAnts, [
            ("--time_series", {"help": "Source time series"}),
            ("--transforms", {"help": "4D motion-correction transform image"}),
            (
                "--reference", 
                {"help": "Reference time-series defining the geometry"}),
            ("--target", {"help": "Target time series"})
        ])
