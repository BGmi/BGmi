#!/usr/bin/env bash

set -ex

python --version
pip --version

curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
export PATH=$HOME/.poetry/bin:$PATH
poetry config settings.virtualenvs.create false
poetry install -E mysql

if [[ "$DB" == "mysql" ]]; then
  mysql -u root -e 'CREATE DATABASE IF NOT EXISTS bgmi DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;';
fi
