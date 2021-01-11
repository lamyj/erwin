import os

import Cython.Build
import setuptools

here = os.path.abspath(os.path.dirname(__file__))

long_description = open(os.path.join(here, "README.md")).read()

setuptools.setup(
    name="qMRI_toolbox",
    
    description="Toolbox to generate quantitative maps from MRI images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    url="https://iris.icube.unistra.fr/gitlab/mondino/qmri_toolbox",
    
    author="J. Lamy, M. Mondino, P. Loureiro de Sousa",
    maintainer="Julien Lamy",
    maintainer_email="lamy@unistra.fr",
    
    license="Other/Proprietary License",
    
    classifiers=[
        "Development Status :: 4 - Beta",
        
        "Environment :: Console",
        
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        
        "License :: Other/Proprietary License",
        
        "Programming Language :: Python :: 3",
        
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    
    keywords = [
        "MRI", "quantitative", 
        "field mapping", "B0", "B1",
        "CBF", "cerebral blood flow", "ASL", "arterial spin labeling", "pASL"
        "diffusion", "DTI", "diffusion tensor", "spherical harmonics",
        "MT", "magnetization transfer",
        "relaxometry", "T1", "VFA", "T2", "bSSFP",
    ],
    
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    ext_modules=Cython.Build.cythonize("src/qMRI_toolbox/mt_map/mpf.pyx"),
    
    python_requires=">=3.5.*,",
    
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    
    # FIXME: dicomifier, sycomore
    install_requires=[
        "cython", "doit", "numpy", "scipy", "spire-pipeline>=1.1.1"],
)
