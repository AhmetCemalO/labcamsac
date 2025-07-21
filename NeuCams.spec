# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['neucams/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('neucams/configs/*', 'neucams/configs'),
        ('neucams/jsonfiles/*', 'neucams/jsonfiles'),
        ('neucams/examples_settings/*', 'neucams/examples_settings'),
    ],
    hiddenimports=[
        # PyQt5 and related
        'PyQt5.sip',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebChannel',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtChart',
        'PyQt5.QtNetwork',
        'PyQt5.QtSvg',
        'PyQt5.QtOpenGL',
        # pyqtgraph and submodules
        'pyqtgraph.exporters',
        'pyqtgraph.widgets',
        'pyqtgraph.graphicsItems',
        'pyqtgraph.imageview',
        'pyqtgraph.opengl',
        # Camera libraries
        'vmbpy',
        'pymba',
        'pco',
        'harvesters',
        'genicam',
        # Scientific/utility libraries
        'tifffile.tifffile',
        'olefile',
        'pytz',
        'dateutil',
        'zmq.backend.cython',
        'scipy._lib.messagestream',
        # Dynamic camera modules (add all camera modules you might load dynamically)
        'neucams.cams.avt_cam',
        'neucams.cams.generic_cam',
        'neucams.cams.pco_cam',
        'neucams.cams.qimaging',
        'neucams.cams.opencv_cam',
        # Add more if you add new camera modules
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='neucams',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='neucams'
) 