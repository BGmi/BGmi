#!/bin/sh
exec aria2c --conf-path=/aria2/aria2.conf --rpc-secret=${ARIA2_TOKEN}
