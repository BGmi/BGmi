#!/usr/bin/env bash

files=$(find ./ -name '*.py')

pyupgrade --py3-plus $files
autoflake --in-place --remove-unused-variables --remove-all-unused-imports $files
isort $files
yapf -i $files
