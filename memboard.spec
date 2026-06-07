# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=numpy_binaries,
    datas=numpy_datas,
    hiddenimports=numpy_hiddenimports + [
        'sounddevice',
        '_sounddevice_data',
        'cffi',
        '_cffi_backend',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MemBoard',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='MemBoard',
)
