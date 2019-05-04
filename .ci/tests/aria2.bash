#!/usr/bin/env bash
set -x

#cd
# start deluge rpc server at 8112

docker build -t aria2 .ci/aria2

container_id=$(docker run -d \
    -p 6800:6800 \
    -e ARIA2_TOKEN=secret \
    -v $HOME/.bgmi/bangumi/:/home/travis/.bgmi/bangumi/ \
    -v `pwd`/.ci/aria2/.aria2/:/aria2/ \
    aria2)

docker logs $container_id

sudo chown -R travis:travis ~/.bgmi

bgmi install --no-web
bgmi config ARIA2_RPC_TOKEN token:secret

bgmi config

coverage run .ci/tests/test_download_delegate.py
