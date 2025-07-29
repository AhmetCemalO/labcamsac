# NeuCams.spec
# build with:  pyinstaller --clean -y NeuCams.spec
import glob, os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# ------------------------------------------------------------------ paths
ENV      = Path(r"C:/ProgramData/Miniconda3/envs/den2")
SITEPKG  = ENV / "Lib" / "site-packages"
LIBBIN   = ENV / "Library" / "bin"
VMB_LIB  = SITEPKG / "vmbpy" / "c_binding" / "lib"
MV       = Path(r"C:/Program Files/MATRIX VISION/mvIMPACT Acquire/bin/x64")

def files(pattern, dest="."):
    return [(str(p), dest) for p in glob.glob(str(pattern))]

# ------------------------------------------------------------------ binaries
binaries = [
    # vmbpy native libs
    *files(VMB_LIB / "GcBase_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "GenApi_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "Log_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "log4cpp_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "MathParser_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "NodeMapData_MD_VC142_v3_2_AVT.dll"),
    *files(VMB_LIB / "VmbC.dll"),
    *files(VMB_LIB / "VmbImageTransform.dll"),
    *files(VMB_LIB / "XmlParser_MD_VC142_v3_2_AVT.dll"),

    # OpenCV Python binding
    *files(SITEPKG / "cv2.cp39-win_amd64.pyd"),

    # Matrix Vision DLLs (so mvGenTLProducer.cti can load)
    *files(MV / "*.dll"),
]

# ------------------------------------------------------------------ data
BASE       = Path(os.path.abspath('.'))
GENTL_SRC  = BASE / "cti_dll"

datas = [
    *files(VMB_LIB / "VmbC.xml"),
    *files("files/neucams/view/*.ui", "neucams/view"),

    # ship your repo's cti_dll folder (if you copied stuff there)
    *[(str(p), "cti_dll") for p in GENTL_SRC.rglob("*")
      if p.is_file() and p.suffix.lower() in (".cti", ".dll")],

    # ensure MV CTIs are there even if you forgot to copy them
    *files(MV / "*.cti", "cti_dll"),
]

# ------------------------------------------------------------------ hidden imports
hiddenimports = [
    "neucams.cams.genicam",
    "pyqtgraph",
] \
+ collect_submodules("pyqtgraph") \
+ collect_submodules("harvesters") \
+ collect_submodules("genicam") \
+ collect_submodules("pco")

block_cipher = None

a = Analysis(
    ["files\\neucams\\__main__.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=['hooks/rthook_env.py'],
    excludes=['pyqtgraph.opengl', 'OpenGL'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="NeuCams",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # don't compress vendor DLLs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,            # no UPX here either
    upx_exclude=[],
    name="NeuCams",
)
