#!/usr/bin/env bash

git clone https://github.com/BGmi/BGmi
cd BGmi
# if you need dev branch or some tag
# git checkout dev
docker build -t bgmi .

alias bgmi='docker run -e BGMI_PATH=$HOME/.bgmi -v $HOME/.bgmi:$HOME/.bgmi --net host bgmi'
alias bgmi_http='docker run -p 127.0.0.1:8888:8888 -e BGMI_PATH=$HOME/.bgmi -v $HOME/.bgmi:$HOME/.bgmi --net host bgmi'
# bootstrap bgmi
bgmi install
# start bgmi http server in back ground
bgmi_http
