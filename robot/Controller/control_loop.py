#!/usr/bin/env python3

# import socket
# import requests
# from sys import argv
import sys
import time

# import ev3dev.ev3 as ev3
# import urllib.request as request

from move import forward, rotate
# import dispenser
import State
import UniquePriorityQueue as uniq
from queue import Empty
from thread_decorator import thread, ThreadKiller
import Directions

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

CHOSEN_PATH = [40,90,40,-90,40] # this is going to be a list of node distances and angles

STATE = State.LOADING

STATE_QUEUE = uniq.UniquePriorityQueue()

# the lower the number, the higher the priority
T_LOADING = (3, State.LOADING)
T_DELIVERING = (3, State.DELIVERING)
T_RETURNING = (2, State.RETURNING)
T_STOPPING = (1, State.STOPPING)
T_PANICKING = (3, State.PANICKING)

# def setup_procedure():
# 	move.initialize_motors()
# 	initialize_2nd_brick()
# 	initialize_connection()
#
# def initialize_2nd_brick():
# 	pass # RPyC setup here
#
# def initialize_connection():
# 	try:
# 		pass # do all the required connection setup here
# 		get_current_instruction()
# 	except IOError:
# 		pass # display a "cannot connect" message to the user
# 	poll_for_instructions()
#
# def get_current_instruction():
# 	global STATE_QUEUE
# 	# global BRACKETS
# 	# global CURRENT_POSITION
# 	# global TARGET_POSITION these also have to be queues
# 	pass # get the current instruction and set the STATE accordingly
#
# @thread
# def poll_for_instructions(): # this can also be an interrupt-based listener, not a polling one
# 	while True:
# 		try:
# 			get_current_instruction()
# 		except IOError:
# 			initialize_connection() # not a deamon, so continues existing after this dies
# 			return
# 		get_current_instruction()
# 		time.sleep(2) # wait 2s between pooling intervals

def control_loop():
	global STATE
	while True:
		if STATE == State.LOADING:
			STATE = loading_loop() # these are going to be blocking
		elif STATE == State.DELIVERING:
			STATE = movement_loop()
		elif STATE == State.RETURNING:
			STATE = movement_loop() # same function as above
		elif STATE == State.STOPPING:
			STATE = stop_loop()
		elif STATE == State.PANICKING:
			STATE = panic_loop()

def loading_loop():
	# pool for "go-ahead" button
	return State.DELIVERING

def check_state(current_state):
	try:
		state = STATE_QUEUE.get_nowait()
	except Empty:
		return None
	else:
		if state[1] != current_state:
			with STATE_QUEUE.mutex:
				STATE_QUEUE.queue.clear()
			return state[1]
		else:
			return None

def movement_loop():
	moving_flag = False
	move_thread = None
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			if move_thread is not None:
				move_thread.stop()
			return new_state

		if not moving_flag:
			moving_flag = True
			move_thread = move_asynch(CURRENT_POSITION, BRACKETS, STATE, CHOSEN_PATH)


# def choose_path(reception = False):
# 	if reception:
# 		CHOSEN_PATH = plan_path(CURRENT_POSITION, 0)
# 	else:
# 		list_of_paths = []
# 		for bracket, table_no in BRACKETS:
# 			list_of_paths.append(plan_path(CURRENT_POSITION, table_no))
# 		global CHOSEN_PATH
# 		CHOSEN_PATH = shotest_path(list_of_paths) # need to return the bracket number, so that we know what is left to deliver
#
# def plan_path(current, destination):
# 	pass # djikstra: this can be either implemented on the brick, or fed from the server
#
# def shortest_path(paths):
# 	pass # returns the shortest path from the path list

@thread
def move_asynch(current_position, brackets, state, chosen_path): #all global returns will have to be passed in queues
	try:
		# if state == State.RETURNING:
		# 	chosen_path = choose_path(reception = True)
		# else:
		# 	chosen_path = choose_path()
		while True:
			distance = chosen_path.pop()
			print("driving")
			drive_success = forward(distance, 50)
			if not drive_success:
				print("panicking")
				STATE_QUEUE.put(T_PANICKING)
				break
			else:
				# if infers reception from brackets and chosen_path and state
				# 	STATE_QUEUE.put(T_LOADING)
				# 	return
				if len(chosen_path) == 0:
					print("stopping")
					STATE_QUEUE.put(T_STOPPING)
					break
					# dispenser.dump(bracket) # need to establish some mapping
					# brackets[bracket] = 0 # a QUEUE!!!!
					# move.turn_around()
					# # if all brackets are assigned to 0, enter RETURNING state
					# 	return
					# chosen_path = choose_path()
				else:
					angle = chosen_path.pop()
					direction = None
					if angle < 0:
						direction = Directions.ROT_LEFT
					else:
						direction = Directions.ROT_RIGHT
					print("turning " + str(direction))
					turn_success = rotate(abs(angle), 50, direction=direction)
					if not turn_success:
						print("panicking")
						STATE_QUEUE.put(T_PANICKING)
						break
					else:
						if len(chosen_path) == 0:
							print("stopping")
							STATE_QUEUE.put(T_STOPPING)
							break
		while True:
			pass
	except ThreadKiller:
		sys.exit()


def panic_loop():
	send_position_to_server()
	return

def send_position_to_server():
	pass

def stop_loop():
	# wait for further instuctons
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			return new_state


if __name__ == "__main__":
	#setup_procedure()
	control_loop()
