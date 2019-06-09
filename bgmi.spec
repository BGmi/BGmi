# -*- mode: python -*-
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
import os
import os.path
import importlib
import glob
from typing import List
bindata_dir = [
    'bgmi/front/templates',
    'bgmi/others',
    'bgmi/lib/db_models/migrations',
    'bgmi.egg-info',
]

import pkg_resources


def do_add(s, element):
    l = len(s)
    s.add(element)
    return len(s) != l


def get_single_package_dependencies(package_name: str) -> List[str]:
    package = pkg_resources.working_set.by_key[package_name]
    return [r.key for r in package.requires()]


def get_package_dependencies(package_name) -> List[str]:
    processed_keys = set()
    unprocessed_keys = set(get_single_package_dependencies(package_name))
    while unprocessed_keys:
        el = unprocessed_keys.pop()
        processed_keys.add(el)
        for pkg in get_single_package_dependencies(el):
            if do_add(unprocessed_keys, pkg):
                continue
    processed_keys.add(package_name)
    return list(processed_keys)


def manually_add_dep_package(package_name):
    f = []
    for pkg_name in get_package_dependencies(package_name):
        f.extend(manually_add_single_dep_package(pkg_name))
    return f


def manually_add_single_dep_package(package_name):
    proot = os.path.dirname(importlib.import_module(package_name).__file__)
    f = []
    for (dirpath, _, filenames) in os.walk(proot):
        f.extend((os.path.join(dirpath, x), package_name) for x in filenames if x.endswith('.py'))
    return f


def get_bindata():
    for dir_path in bindata_dir:
        for file in os.listdir(dir_path):
            yield (os.path.join(dir_path, file), dir_path)


block_cipher = None

package_imports = [['peewee_migrate', ['template.txt']]]
datas = list(get_bindata())
datas.extend(manually_add_single_dep_package('pydantic'))

for package, files in package_imports:
    proot = os.path.dirname(importlib.import_module(package).__file__)
    datas.extend((os.path.join(proot, f), package) for f in files)

a = Analysis(['bgmi/__main__.py'],
             pathex=['.'],
             hiddenimports=['colorsys', 'dataclasses', 'distutils', 'distutils.version'],
             hookspath=None,
             datas=datas,
             excludes=['pydantic'],
             runtime_hooks=None,
             cipher=block_cipher)

# for pkg in a.pure:
#     print(pkg)

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
