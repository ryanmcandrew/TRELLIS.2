from setuptools import setup
from torch.utils.cpp_extension import CUDAExtension, BuildExtension, IS_HIP_EXTENSION
import os
import sys
import platform

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_TARGET = os.environ.get("BUILD_TARGET", "auto")

if BUILD_TARGET == "auto":
    if IS_HIP_EXTENSION:
        IS_HIP = True
    else:
        IS_HIP = False
else:
    if BUILD_TARGET == "cuda":
        IS_HIP = False
    elif BUILD_TARGET == "rocm":
        IS_HIP = True

if not IS_HIP:
    cc_flag = []
else:
    # Prefer explicit GPU_ARCHS; 'native' relies on offload-arch.exe which may fail
    archs = os.getenv("GPU_ARCHS", "gfx1031").split(";")
    cc_flag = [f"--offload-arch={arch}" for arch in archs]

# Eigen: use the git submodule if populated, otherwise fall back to conda-installed eigen
def _find_eigen():
    submodule = os.path.join(ROOT, "third_party/eigen")
    if os.path.isdir(os.path.join(submodule, "Eigen")):
        return [submodule]
    # conda install -c conda-forge eigen puts headers at <prefix>/Library/include/eigen3
    conda_eigen = os.path.join(sys.prefix, "Library", "include", "eigen3")
    if os.path.isdir(conda_eigen):
        return [conda_eigen]
    # Some layouts put Eigen/ directly under Library/include
    conda_inc = os.path.join(sys.prefix, "Library", "include")
    if os.path.isdir(os.path.join(conda_inc, "Eigen")):
        return [conda_inc]
    # Submodule exists but may just be empty; include it anyway so error is clear
    return [submodule]

eigen_include = _find_eigen()

setup(
    name="o_voxel",
    packages=[
        'o_voxel',
        'o_voxel.convert',
        'o_voxel.io',
    ],
    ext_modules=[
        CUDAExtension(
            name="o_voxel._C",
            sources=[
                # Stub to supply c10::ValueError ctor missing from TheRock c10.dll
                os.path.join(ROOT, "src/c10_compat.cpp"),
                # Hashmap functions
                "src/hash/hash.cu",
                # Convert functions
                "src/convert/flexible_dual_grid.cpp",
                "src/convert/volumetic_attr.cpp",
                ## Serialization functions
                "src/serialize/api.cu",
                "src/serialize/hilbert.cu",
                "src/serialize/z_order.cu",
                # IO functions
                "src/io/svo.cpp",
                "src/io/filter_parent.cpp",
                "src/io/filter_neighbor.cpp",
                # Rasterization functions
                "src/rasterize/rasterize.cu",

                # main
                "src/ext.cpp",
            ],
            include_dirs=eigen_include,
            extra_compile_args=(
                {
                    "cxx": ["/O2", "/std:c++17", "/EHsc", "/Zc:__cplusplus"],
                    "nvcc": ["-O3", "-std=c++17"] + ([] if IS_HIP else ["-Xcompiler=/std:c++17", "-Xcompiler=/EHsc", "-Xcompiler=/permissive-", "-Xcompiler=/Zc:__cplusplus"]) + cc_flag,
                }
                if platform.system() == "Windows"
                else {
                    "cxx": ["-O3", "-std=c++17"],
                    "nvcc": ["-O3", "-std=c++17"] + cc_flag,
                }
            )
        )
    ],
    cmdclass={
        'build_ext': BuildExtension
    }
)
