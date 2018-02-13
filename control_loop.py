#!/usr/bin/env python3

import socket
import requests
from sys import argv

import ev3dev.ev3 as ev3
import urllib.request as request

#---communications
#------------------

#Internet connection needs to be established first, this has to be check by the ev3 (this has to be re-checked if the connection is lost)

#Set-up communication at the beginning of the control loop. Polling for access to the website before the robot progress commences


#--intra-brick-network
#------------------



#---barcode scanning 
#------------------

#[Placeholder ATM] for the third client demo


#---path planning 
#------------------

#{(recieves the path plan for the robot (on the output of the Deliver Mail button))}



#---move code 
#------------------

#{The dispensing code will have to be integrated with line sensing which is managed by the move code currently}
#{Website sends post requests which directly effect the robot's movement}


#---dispensing code
#------------------



 
