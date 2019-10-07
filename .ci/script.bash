#!/usr/bin/env bash

set -ex

python --version
pip freeze

mkdir -p ~/data
curl -L https://github.com/BGmi/BGmi/releases/download/test-data/data-1.sql -o ~/data/db.sql
export DB_SQL_PATH=~/data/db.sql

coverage run -a -m bgmi install --no-web

codecov --flags command > /dev/null
rm .coverage codecov.yml -f||true # macos's rm return 0 with f flag when file doesn't exists

#  bash tests/init_env_and_run_unit_test.sh test_data_source

bash tests/init_env_and_run_unit_test.sh test_controllers
#   UNITTEST=1 BGMI_LOG=info coverage run -a -m unittest tests.test_http_api -v

cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py

codecov --flags unittest > /dev/null
rm .coverage codecov.yml -f||true

chmod +x .ci/command_test.bash
./.ci/command_test.bash

codecov --flags command > /dev/null
rm .coverage codecov.yml -f||true
