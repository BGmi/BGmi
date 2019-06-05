#!/usr/bin/env bash

set -ex

pip install -e .
pyinstaller bgmi.spec --distpath ./dist/binary/
pip uninstall -y bgmi
