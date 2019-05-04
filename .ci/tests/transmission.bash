#!/usr/bin/env bash
set -x
docker build -t transmission .ci/transmission

docker run -d \
    -p 9091:9091 \
    -v $HOME/.bgmi/bangumi/:/home/travis/.bgmi/bangumi/ \
    transmission

sudo chown -R travis:travis ~/.bgmi

bgmi install --no-web
bgmi config DOWNLOAD_DELEGATE transmission-rpc
bgmi config TRANSMISSION_RPC_USERNAME username
bgmi config TRANSMISSION_RPC_PASSWORD password
bgmi config

python .ci/tests/test_download_delegate.py
