#!/bin/bash

if [ $# -lt 2 ]; then
    echo 'Usage: ./docker.sh <HOME DIR> <ARIA2 TOKEN>'
    exit 1
fi

HOME=$1
TOKEN=$2

echo Setup token ...
bgmi config ARIA2_RPC_TOKEN token:$TOKEN

echo Build docker ...
docker build -t bgmi .

echo Running docker ...
CONTAINER=$(docker run -p127.0.0.1:8888:80 -p6800:6800 -d -v $HOME/.bgmi:$HOME/.bgmi bgmi)

docker exec -it $CONTAINER ln -s ~/.bgmi/ /bgmi
docker exec -it $CONTAINER bash -c 'echo rpc-secret=token:$TOKEN >> /root/aria2c.conf'

echo "Input followed command (without '>'):"
echo '> restart bgmi:aria2c'
echo '> quit'

docker exec -it $CONTAINER supervisorctl


