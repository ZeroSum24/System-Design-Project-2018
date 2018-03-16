#! /bin/bash

sudo apt update
sudo apt upgrade

sudo apt install python3 python3-pip mosquitto nano make g++ emacs24 python3-dev htop libzbar-dev libdmtx0a

pip3 install -r requirements.txt

curl https://getcaddy.com | bash -s personal hook.service

sudo caddy -service install -conf Caddyfile
sudo caddy -service start

export FLASK_APP=spam.py
export DEV_ACCESS_TOKEN='2ad4f817b64442e08cb03d783394746c'
export CLIENT_ACCESS_TOKEN='230a5f0ab9094da381916abe10264faa'

nohup python3 -m flask run --host=0.0.0.0 --port=5000 &
