#!/bin/sh
# This is a script to automate access to the experimental server

chmod 400 "SDP_GROUP_KEY_2.pem"
ssh -i "SDP_GROUP_KEY_2.pem" ubuntu@18.219.97.244
