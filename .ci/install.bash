#!/usr/bin/env bash

set -ex

python --version
pip --version

if [[ $TRAVIS_OS_NAME == "osx" ]]; then
  pip install --upgrade certifi
  pip install -U poetry
else
  curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
fi

export PATH=$HOME/.poetry/bin:$PATH
pip install toml==0.10.0
python .circleci/export_requirements.py --all
pip install --no-deps -r requirements.txt
poetry config settings.virtualenvs.create false
poetry install -E mysql

if [[ "$DB" == "mysql" ]]; then
  mysql -u root -e 'CREATE DATABASE IF NOT EXISTS bgmi DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;';
fi
