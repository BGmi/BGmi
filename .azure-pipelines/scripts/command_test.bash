#!/usr/bin/env bash
set -ex

rm -rf ~/.bgmi || true
coverage run -a -m bgmi install
cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py

coverage run -a -m bgmi --help
coverage run -a -m bgmi gen nginx.conf --server-name _
coverage run -a -m bgmi cal -f
coverage run -a -m bgmi cal
coverage run -a -m bgmi config ADMIN_TOKEN 233
coverage run -a -m bgmi config DOWNLOAD_DELEGATE 'aria2-rpc'
coverage run -a -m bgmi config GLOBAL_FILTER 'Leopard-Raws, hevc, x265, c-a Raws, 外挂'
coverage run -a -m bgmi config
coverage run -a -m bgmi add ${BANGUMI_1} ${BANGUMI_2}
coverage run -a -m bgmi update
coverage run -a -m bgmi delete ${BANGUMI_2}
coverage run -a -m bgmi add ${BANGUMI_2}
coverage run -a -m bgmi add ${BANGUMI_1} ${BANGUMI_2}
coverage run -a -m bgmi add ${BANGUMI_2} --episode 1
coverage run -a -m bgmi fetch ${BANGUMI_2}
coverage run -a -m bgmi list
coverage run -a -m bgmi mark ${BANGUMI_2} 1
coverage run -a -m bgmi update ${BANGUMI_2}
coverage run -a -m bgmi filter ${BANGUMI_2} --subtitle "" --exclude "MKV" --regex "720p|720P"
coverage run -a -m bgmi fetch ${BANGUMI_2}
coverage run -a -m bgmi search ${BANGUMI_2} --regex-filter '.*MP4.*720P.*' --min-episode 800 --max-episode 900
