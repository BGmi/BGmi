#!/usr/bin/env bash
set -ex

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then

    if [[ $TRAVIS_PYTHON_VERSION == '3.7' ]];then
        PYTHON_PKG='https://www.python.org/ftp/python/3.7.3/python-3.7.3-macosx10.9.pkg'
    elif [[ $TRAVIS_PYTHON_VERSION == '3.6' ]];then
        PYTHON_PKG='https://www.python.org/ftp/python/3.6.8/python-3.6.8-macosx10.9.pkg'
    else
        exit 1
    fi

    wget ${PYTHON_PKG} -O $HOME/python.pkg
    sudo installer -verbose -pkg $HOME/python.pkg -target /

    curl https://bootstrap.pypa.io/get-pip.py -o $HOME/get-pip.py
    python3 $HOME/get-pip.py

    python3 -m pip install virtualenv
    python3 -m virtualenv $HOME/venv
    source $HOME/venv/bin/activate
    python -m pip install -U pip

fi
