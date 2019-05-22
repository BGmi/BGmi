# -*- mode: python -*-
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis

import os
import importlib

block_cipher = None

package_imports = [['peewee_migrate', ['template.txt']]]

datas = []

for package, files in package_imports:
    proot = os.path.dirname(importlib.import_module(package).__file__)
    datas.extend((os.path.join(proot, f), package) for f in files)

a = Analysis(['bin/bgmi'],
             pathex=['.'],
             hiddenimports=[],
             hookspath=None,
             datas=datas,
             runtime_hooks=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='bgmi',
    debug=False,
    strip=None,
    upx=True,
    console=True,
    bootloader_ignore_signals=True,
)
