#!/usr/bin/env bash

pyinstaller bgmi.spec --distpath ./dist/binary/

./dist/binary/bgmi --help # || cat build/bgmi/warn-bgmi.txt
