#!/usr/bin/env bash

set -ex

BANGUMI_1=名侦探柯南
BANGUMI_2=妖怪手表
BANGUMI_3=海贼王

python --version
pip freeze

if [[ "$DB" == "mysql" ]]; then
  export BGMI_DB_URL='mysql+pool://root:@127.0.0.1:3306/bgmi?charset=utf8mb4';
fi

coverage run -a -m bgmi install --no-web;

bash <(curl -s https://codecov.io/bash) -c -F command > /dev/null

bash tests/init_env_and_run_unit_test.sh test_utils
bash tests/init_env_and_run_unit_test.sh test_models

if [[ "$DB" == "mysql" ]]; then
  exit
fi

#  bash tests/init_env_and_run_unit_test.sh test_data_source

bash tests/init_env_and_run_unit_test.sh test_controllers
bash tests/init_env_and_run_unit_test.sh test_config
bash tests/init_env_and_run_unit_test.sh test_download_delegate
#   UNITTEST=1 BGMI_LOG=info coverage run -a -m unittest tests.test_http_api -v


bash tests/init_env_and_run_unit_test.sh test_website

cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py

bash <(curl -s https://codecov.io/bash) -c -F unittests > /dev/null

bash ./.ci/command_test.bash
bash <(curl -s https://codecov.io/bash) -c -F command > /dev/null
