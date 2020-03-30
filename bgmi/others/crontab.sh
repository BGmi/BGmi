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

crontab -l | grep "bgmi update" > /dev/null
if [ $? -eq 0 ]; then
    echo "[-] crontab update already exist";
else
    (crontab -l;printf "0 */2 * * * LC_ALL=en_US.UTF-8 $BGMI_PATH update $DOWNLOAD\n")|crontab -
    echo "[+] crontab update added"
fi


crontab -l | grep "bgmi cal" > /dev/null
if [ $? -eq 0 ]; then
    echo "[-] crontab update cover already exist";
else
    (crontab -l;printf "0 */10 * * * LC_ALL=en_US.UTF-8 TRAVIS_CI=1 $BGMI_PATH cal --force-update --download-cover\n")|crontab -
    echo "[+] crontab update cover added"
fi
