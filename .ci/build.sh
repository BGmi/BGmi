#!/usr/bin/env bash

pyinstaller bgmi.spec

./dist/bgmi --help # || cat build/bgmi/warn-bgmi.txt
