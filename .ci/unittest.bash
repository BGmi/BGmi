#!/usr/bin/env bash

set -ex

python --version
pip freeze

if [[ "$DB" == "mysql" ]]; then
  export BGMI_DB_URL='mysql+pool://root:@127.0.0.1:3306/bgmi?charset=utf8mb4';
fi

bgmi install --no-web;

bash tests/init_env_and_run_unit_test.sh test_utils
bash tests/init_env_and_run_unit_test.sh test_db_models

if [[ "$DB" == "mysql" ]]; then
  exit
fi

#  bash tests/init_env_and_run_unit_test.sh test_data_source

bash tests/init_env_and_run_unit_test.sh test_controllers
bash tests/init_env_and_run_unit_test.sh test_config
#   UNITTEST=1 BGMI_LOG=info coverage run -a -m unittest tests.test_http_api -v

cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py
