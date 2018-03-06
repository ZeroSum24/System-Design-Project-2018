#!/bin/sh
# This is a script to automate access to the experimental server

chmod 400 "SDP_GROUP_KEY.pem.txt"
scp -i "SDP_GROUP_KEY.pem.txt" ubuntu@34.242.137.167:/home/ubuntu/sdp2018/spam/spam/image.jpg /afs/inf.ed.ac.uk/user/s13/s1346249/Desktop/sdp2018/spam/spam/Image_Test/imgs/server_images
