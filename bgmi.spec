# -*- mode: python -*-
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis

block_cipher = None
datas = [("./bgmi.egg-info/*", "bgmi.egg-info")]

a = Analysis(
    ["bgmi/__main__.py"],
    hiddenimports=["bgmi"],
    hookspath=None,
    runtime_hooks=None,
    binaries=datas,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher,)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="bgmi",
    debug=False,
    strip=None,
    upx=True,
    console=True,
    bootloader_ignore_signals=True,
)
