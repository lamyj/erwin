import itertools

import spire

################
# Tensor model #
################

class DiffusionTensor(spire.TaskFactory):
    def __init__(self, source, target, mask=None)
    file_dep = (
        dwi_preprocessing.Preprocessing.targets 
        + dwi_preprocessing.DiffusionMask.targets)
    targets = [final/"dt.mif.gz"]
    actions = [
        [
            "dwi2tensor", "-force", "-quiet", 
            "-mask", file_dep[1], file_dep[0], targets[0]]]

# class DiffusionTensorMetrics(spire.Task):
#     metrics = ["adc", "fa", "ad", "rd"]
#     file_dep = (
#         DiffusionTensor.targets + dwi_preprocessing.DiffusionMask.targets)
#     targets = [final/"{}.nii.gz".format(metric) for metric in metrics]
#     actions = [
#         [
#             "tensor2metric", "-force", "-quiet", 
#             "-mask", file_dep[1], file_dep[0]]
#         +list(itertools.chain(*[
#             ["-{}".format(metric), "{}".format(target)] 
#             for metric, target in zip(metrics, targets)]))
#     ]
# 
# #############################
# # Spherical harmonics model #
# #############################
# 
# # DWI-based response estimation
# # As of Mrtrix 3.0.0, this is the "improved" Dhollander method.
# class SphericalHarmonicsResponse(spire.TaskFactory):
#     file_dep = dwi_preprocessing.Preprocessing.targets
#     targets = [final/"wm.response", final/"gm.response", final/"csf.response"]
#     actions = [
#         [
#             "dwi2response", "dhollander", "-force", "-quiet"]+file_dep+targets]
# 
# class SphericalHarmonics(spire.TaskFactory):
#     file_dep = dwi_preprocessing.Preprocessing.targets + [
#         "../global/{}.response".format(x) for x in ["wm", "gm", "csf"]]
#     targets = [final/"sh_wm.mif.gz", final/"sh_gm.mif.gz", final/"sh_csf.mif.gz"]
#     actions = [
#         ["echo", "WARNING: make sure the global response is up-to-date"],
#         ["dwi2fod", "-force", "-quiet", "msmt_csd", file_dep[0]]
#             +list(itertools.chain(*zip(file_dep[1:], targets)))
#     ]
# 
# class GlobalIntensityNormalisation(spire.TaskFactory):
#     file_dep = (
#         SphericalHarmonics.targets+dwi_preprocessing.DiffusionMask.targets)
#     targets = [
#         str(x).replace(".mif.gz", "_norm.mif.gz") 
#         for x in SphericalHarmonics.targets]
#     actions = [
#         ["mtnormalise", "-force", "-quiet", "-mask", file_dep[-1]]
#             +list(itertools.chain(*zip(file_dep[:-1], targets)))
#     ]
# 
# fixels = final/"fixels"
# 
# class FODFixels(spire.TaskFactory):
#     file_dep = [GlobalIntensityNormalisation.targets[0]]
#     targets = [
#         fixels/"{}.mif.gz".format(x) for x in ["afd", "peak", "dispersion"]]
#     actions = [
#         ["rm", "-rf", fixels],
#         [
#             "fod2fixel", "-force", "-quiet", 
#             "-afd", targets[0].name, "-peak", targets[1].name, 
#             "-disp", targets[2].name, 
#             file_dep[0], fixels
#         ]
#     ]
# 
# class AFD(spire.TaskFactory):
#     file_dep = [FODFixels.targets[0]]
#     targets = [final/"afd.nii.gz"]
#     actions = [
#         ["fixel2voxel", "-quiet", "-force", file_dep[0], "mean", targets[0]],
#         ["ImageMath", "4", targets[0], "ExtractSlice", targets[0], "0"]
#     ]
