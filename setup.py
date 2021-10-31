import os

import Cython.Build
import setuptools

here = os.path.abspath(os.path.dirname(__file__))

long_description = open(os.path.join(here, "README.md")).read()

setuptools.setup(
    name="erwin",
    version="1.0.0-pre1",
    
    description="Toolbox to generate quantitative maps from MRI images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    url="https://github.com/lamyj/erwin",
    
    author="J. Lamy, M. Mondino, P. Loureiro de Sousa",
    maintainer="Julien Lamy",
    maintainer_email="lamy@unistra.fr",
    
    license="MIT",
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        
        "Environment :: Console",
        
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        
        "License :: OSI Approved :: MIT License",
        
        "Programming Language :: Python :: 3",
        
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    
    keywords = [
        "MRI", "quantitative", 
        "field mapping", "B0", "B1",
        "CBF", "cerebral blood flow", "ASL", "arterial spin labeling", "pASL",
        "diffusion", "DTI", "diffusion tensor", "spherical harmonics",
        "MT", "magnetization transfer",
        "relaxometry", "T1", "VFA", "T2", "bSSFP",
    ],
    
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    ext_modules=Cython.Build.cythonize([
        setuptools.Extension(
            "erwin.mt_map.mpf", ["src/erwin/mt_map/mpf.pyx"])
    ]),
    
    python_requires=">=3.5",
    
    install_requires=[
        "cython", "dmri-amico", "doit", "meg", "nibabel", "numpy", "scipy",
        "spire-pipeline>=1.1.1", "sycomore"],
    
    entry_points={ "console_scripts": [ "erwin=erwin.__main__:main"] },
)
