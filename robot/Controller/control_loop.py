#!/usr/bin/env python3

import socket
import requests
from sys import argv
import time
from queue import Queue

import ev3dev.ev3 as ev3
import urllib.request as request

from move import forward, select_junction, initialize_motors
import State

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




# temporary bracket-desk mapping, could indicate empty with 0 and have desk number otherwise
BRACKETS = {1 : 0, 2 : 0, 3 : 0, 4 : 0, 5 : 0}

CURRENT_POSITION = 0 # current node number

CHOSEN_PATH = 0 # this is going to be a dictionary of nodes and angles

STATE_QUEUE = Queue(1)

MOVING_FLAG = False # flag indicating whether the robot is moving

STATE = State.LOADING

def setup_procedure():
	move.initialize_motors()
	initialize_2nd_brick()
	initialize_connection()

def initialize_2nd_brick():
	pass # RPyC setup here

def initialize_connection():
	try:
		pass # do all the required connection setup here
		get_current_instruction()
	except IOError:
		pass # display a "cannot connect" message to the user
	poll_for_instructions()

def get_current_instruction():
	global STATE_QUEUE
	global BRACKETS
	global CURRENT_POSITION
	global TARGET_POSITION
	pass # get the current instruction and set the STATE accordingly

@thread
def poll_for_instructions(): # this can also be an interrupt-based listener, not a polling one
	while True:
		# if (lost_connection):
		# 	initialize_connection()
		# 	return
		get_current_instruction()
		time.sleep(2) # wait 2s between pooling intervals

def control_loop():
	global STATE
	while True:
		if STATE = State.LOADING:
			STATE = loading_loop() # these are going to be blocking
		elif STATE = State.DELIVERING:
			STATE = delivery_loop()
		elif STATE = State.RETURNING:
			STATE = return_loop()
		elif STATE = State.PANIC:
			STATE = panic_loop()

def loading_loop():
	# pool for "go-ahead" button
	pass

def delivery_loop(): # queue-ception to move and back
	global MOVING_FLAG
	while True:
		try:
			state = STATE_QUEUE.get_nowait()
			STATE = state
		except Empty:
			pass

		if MOVING_FLAG:
			MOVING_FLAG = False
			choose_path()
			move()
	return State.RETURNING

def choose_path():
	list_of_paths = []
	for bracket, table_no in BRACKETS:
		list_of_paths.append(plan_path(CURRENT_POSITION, table_no))
	global CHOSEN_PATH
	CHOSEN_PATH = shortest_path(list_of_paths)

def plan_path():
	pass # djikstra: this can be either implemented on the brick, or fed from the server

def shortest_path():
	pass # returns the shortest path from the path list

@thread
def move():
	pass # move, junction, dispense

def panic_loop():
	pass

def return_loop():
	# path
	pass


if __name__ = "__main__":
	setup_procedure()
	control_loop()
