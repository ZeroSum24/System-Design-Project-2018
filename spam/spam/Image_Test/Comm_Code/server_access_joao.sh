#!/bin/sh
# This is a script to automate access to the experimental server

chmod 400 "SDP_GROUP_KEY.pem.txt"
ssh -i "SDP_GROUP_KEY.pem.txt" ubuntu@34.242.137.167
