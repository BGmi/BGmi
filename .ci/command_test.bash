#!/usr/bin/env bash
set -ex

rm -rf ~/.bgmi | true
bgmi install
cp tests/test_script.py $HOME/.bgmi/scripts/test_script.py

bgmi --help
bgmi gen nginx.conf --server-name _
bgmi cal -f
bgmi cal
bgmi config
bgmi config ADMIN_TOKEN 233
bgmi config DOWNLOAD_DELEGATE 'aria2-rpc'
bgmi config GLOBAL_FILTER 'Leopard-Raws, hevc, x265, c-a Raws, 外挂'
bgmi add ${BANGUMI_1} ${BANGUMI_2} ${BANGUMI_3}
bgmi update
bgmi delete ${BANGUMI_3}
bgmi add ${BANGUMI_1} ${BANGUMI_2}
bgmi add ${BANGUMI_2} --episode 1
bgmi fetch ${BANGUMI_2}
bgmi list
bgmi mark ${BANGUMI_2} 1
bgmi update ${BANGUMI_2}
bgmi filter ${BANGUMI_2} --subtitle "" --exclude "MKV" --regex "720p|720P"
bgmi fetch ${BANGUMI_2}
bgmi search "海贼王" --regex-filter '.*MP4.*720P.*' --min-episode 800 --max-episode 900
