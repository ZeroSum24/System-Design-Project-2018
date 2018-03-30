#!/usr/bin/env bash

set -eu

if [[ -z ${DEBUG+x} ]]; then
    debug=echo
else
    debug=:
fi

sudo apt-get install -y python3-setuptools
tar -xvf mqtt.tar
cd mqtt
sudo python3 setup.py install
cd ..
sudo rm -rf ./mqtt
