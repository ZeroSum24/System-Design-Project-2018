#!/bin/sh
# This is a script to automate getting the sent image from the main server

chmod 400 "SDP_GROUP_KEY.pem.txt"
scp -i "SDP_GROUP_KEY.pem.txt" ubuntu@34.242.137.167:/home/ubuntu/sdp2018/spam/spam/image_recieved.jpg ../imgs/server_images
