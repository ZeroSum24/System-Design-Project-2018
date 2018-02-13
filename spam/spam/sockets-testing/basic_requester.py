#!/usr/bin/env python3

import socket
import requests
from sys import argv

import ev3dev.ev3 as ev3
import urllib.request as request

#set-up at the beginning of the control loop. Polling for access to the
#website before the robot progress commences

#internet connection needs to be established first
#this has to be check by the ev3


#open a loop to a continue until website sends back a confirmation (to be
#established on the flask end, they will record ip-address of robot at this)
#final website 'http://ec2-34-245-88-253.eu-west-1.compute.amazonaws.com'

#https://pythonspot.com/python-network-sockets-programming-tutorial/

TCP_IP = '127.0.0.1'
TCP_PORT = 5000
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

button = ev3.Button()
while button.any() == False:

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))

    #payload = (('key1', 'value1'), ('key1', 'value2'))
    payload = "Hello, World!"
    r = requests.post('http://127.0.0.1:5000/handle_data', data=payload)
    #data = s.recv(BUFFER_SIZE)
    data = s.recv(BUFFER_SIZE)

    # if (data == "Hello, World!"):
    if (r.text = "Hello, World!"):
        print("Eureka! Connnection has been established")
    else:
	       print "Keep trying Steve!"
    s.close()
# above is an alternative method 
