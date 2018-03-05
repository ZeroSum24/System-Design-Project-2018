#!/bin/sh
# This is a script to automate access to the experimental server

chmod 400 "SDP_GROUP_KEY_2.pem"
scp -i "SDP_GROUP_KEY_2.pem" spam.db ubuntu@18.219.97.244:/home/ubuntu/sdp2018/spam
