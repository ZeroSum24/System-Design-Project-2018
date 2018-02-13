#!/usr/bin/env python3

import socket
import requests
from sys import argv

TCP_IP = '127.0.0.1'
TCP_PORT = 5000
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

if (data == 1):
	print "Eureka! Connnection has been established"
else: 
	print "Keep trying Steve!"



