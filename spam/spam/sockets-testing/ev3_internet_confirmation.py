#!/usr/bin/env python3

#Pings google.com to establish whether internet connection has been established on the brick
#This should be part of start-up protocol on the Control Loop

import shlex
import subprocess

# Tokenize the shell command
# cmd will contain  ["ping","-c1","google.com"]
cmd=shlex.split("ping -c1 google.com")

try:
   output = subprocess.check_output(cmd)
   print (output)
except subprocess.CalledProcessError:
   #Will print the command failed with its exit status
   print ("Internet is not connected. Please re-check Internet Connection", format(cmd[-1]))
else:
   internet_connected = True # can remove this statement and place in ev3 sender code

#Once the internet is connected begin with flask code
