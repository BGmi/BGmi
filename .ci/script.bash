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

rm -rf ~/.bgmi | true
coverage run -a -m bgmi install
cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py

bgmi --help
coverage run -a -m bgmi gen nginx.conf --server-name _
coverage run -a -m bgmi cal -f
coverage run -a -m bgmi cal
coverage run -a -m bgmi config
coverage run -a -m bgmi config ADMIN_TOKEN 233
coverage run -a -m bgmi config DOWNLOAD_DELEGATE 'aria2-rpc'
coverage run -a -m bgmi add ${BANGUMI_1} ${BANGUMI_2} ${BANGUMI_3}
coverage run -a -m bgmi update
coverage run -a -m bgmi delete --name ${BANGUMI_3}
coverage run -a -m bgmi delete --clear-all --batch
coverage run -a -m bgmi add ${BANGUMI_2} --episode 1
coverage run -a -m bgmi fetch ${BANGUMI_2}
coverage run -a -m bgmi list
coverage run -a -m bgmi mark ${BANGUMI_2} 1
coverage run -a -m bgmi update ${BANGUMI_2}
coverage run -a -m bgmi filter ${BANGUMI_2} --subtitle "" --exclude "MKV" --regex "720p|720P"
coverage run -a -m bgmi fetch ${BANGUMI_2}
coverage run -a -m bgmi search "海贼王" --regex-filter '.*MP4.*720P.*' --min-episode 800 --max-episode 900
eval "$(coverage run -a -m bgmi complete)"

bash <(curl -s https://codecov.io/bash) -c -F command > /dev/null
