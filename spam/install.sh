#!/usr/bin/env bash

. ../ip.conf

sed -i "1 s/.*/$domain, www.$domain {/" Caddyfile

sudo apt update
sudo apt upgrade -y

sudo apt install -y python3 python3-pip mosquitto nano make g++ emacs24 python3-dev htop libzbar-dev libdmtx0a

pip3 install -r ../requirements.txt

curl https://getcaddy.com | bash -s personal
sudo nohup caddy &

cd ..
make
cd ./spam

export FLASK_APP=spam.py
export DEV_ACCESS_TOKEN='2ad4f817b64442e08cb03d783394746c'
export CLIENT_ACCESS_TOKEN='230a5f0ab9094da381916abe10264faa'

sudo nohup python3 -m flask run --host=0.0.0.0 --port=5000 &
