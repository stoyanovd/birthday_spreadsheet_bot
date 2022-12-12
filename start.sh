#!/bin/bash
echo "Running..."
sudo pkill -F ./pid.pid
sudo python ./goes.py &
echo $! > ./pid.pid