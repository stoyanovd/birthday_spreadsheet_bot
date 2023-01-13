#!/bin/bash
echo "Running..."
pkill -F ./pid.pid
python ./goes.py & echo $! > ./pid.pid

