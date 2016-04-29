#!/bin/sh
BGMI_PATH=$(which bgmi)
DOWNLOAD="--download"

usage(){
    echo "Usage: sh crontab.sh [options]\n"
    echo "Options:\n  --no-download\t\tNot download bangumi when updated"
    exit
}

if [ $# -ne 1 -a $# -ne 0 ]; then
    usage
fi

if [ $# -eq 1 -a "$1" != "--no-download" ]; then
    usage
fi

if [ $# -eq 1 -a "$1" = "--no-download" ]; then
    DOWNLOAD=""
fi

(crontab -l;printf "* */2 * * * $BGMI_PATH update $DOWNLOAD\n")|crontab -
echo "crontab added"