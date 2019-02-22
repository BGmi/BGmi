#!/usr/bin/env bash
TEST_CASE=$1

BGMI_PATH=~/.bgmi/

if [[ -d "$BGMI_PATH" ]]; then
    rm ${BGMI_PATH} -rf
    echo "remove BGMI_PATH"
fi

python -m bgmi > /dev/null

UNITTEST=1 BGMI_LOG=info coverage run -a -m unittest tests.${TEST_CASE} -v

