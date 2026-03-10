# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = [('python64\\Lib\\site-packages\\paddle\\libs', 'paddle\\libs')]
binaries = [('python64\\Lib\\site-packages\\nvidia\\cuda_runtime\\bin\\*.dll', 'nvidia\\cuda_runtime\\bin'), ('python64\\Lib\\site-packages\\nvidia\\cudnn\\bin\\*.dll', 'nvidia\\cudnn\\bin'), ('python64\\Lib\\site-packages\\nvidia\\cublas\\bin\\*.dll', 'nvidia\\cublas\\bin'), ('python64\\Lib\\site-packages\\nvidia\\cufft\\bin\\*.dll', 'nvidia\\cufft\\bin'), ('python64\\Lib\\site-packages\\nvidia\\curand\\bin\\*.dll', 'nvidia\\curand\\bin'), ('python64\\Lib\\site-packages\\nvidia\\cusolver\\bin\\*.dll', 'nvidia\\cusolver\\bin'), ('python64\\Lib\\site-packages\\nvidia\\cusparse\\bin\\*.dll', 'nvidia\\cusparse\\bin'), ('python64\\Lib\\site-packages\\nvidia\\nvjitlink\\bin\\*.dll', 'nvidia\\nvjitlink\\bin')]
hiddenimports = ['framework_pb2']
datas += copy_metadata('paddlex')
datas += copy_metadata('paddleocr')
datas += copy_metadata('imagesize')
datas += copy_metadata('opencv-contrib-python')
datas += copy_metadata('pyclipper')
datas += copy_metadata('pypdfium2')
datas += copy_metadata('python-bidi')
datas += copy_metadata('shapely')
tmp_ret = collect_all('paddleocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddlex')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddle')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['paddle.tensorrt'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Win_OCR_v5_Release',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Win_OCR_v5_Release',
)
