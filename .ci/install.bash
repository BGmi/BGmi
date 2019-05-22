#!/usr/bin/env bash

set -ex

python --version
pip --version

pip install -q -r requirements/dev.txt
pip install -q codecov
pip install -e .

if [[ "$DB" == "mysql" ]]; then
  mysql -u root -e 'CREATE DATABASE IF NOT EXISTS bgmi DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;';
  pip install pymysql;
fi
