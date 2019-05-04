#!/usr/bin/env bash
set -x

# start deluge rpc server at 8112
docker run -d\
    --net=host \
    -e PUID=`id -u`\
    -e PGID=`id -g` \
    --restart unless-stopped \
    -v $HOME/.bgmi/bangumi/:/home/travis/.bgmi/bangumi/ \
    linuxserver/deluge

sudo chown -R travis:travis ~/.bgmi

bgmi install --no-web
bgmi config DOWNLOAD_DELEGATE deluge-rpc
bgmi config

python .ci/tests/test_download_delegate.py
