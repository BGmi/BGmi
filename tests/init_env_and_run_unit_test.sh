#!/usr/bin/env bash
TEST_CASE=$1

UNITTEST=1 BGMI_LOG=info coverage run -a -m unittest tests.${TEST_CASE} -v
