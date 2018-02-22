#!/usr/bin/env python3

# import socket
# import requests
# from sys import argv
import sys
import time

# import ev3dev.ev3 as ev3
# import urllib.request as request

from move import forward, rotate, left, right, approach, stop_motors, get_odometry
# import dispenser
import State
import UniquePriorityQueue as uniq
from queue import Empty
from thread_decorator import thread, ThreadKiller, acknowledge
import Directions
import Junctions
import paho.mqtt.client as mqtt
import pickle
from threading import Lock
from Commands import Report, Move, Rotate, Dump

CHOSEN_PATH = None
chosen_path_lock = Lock()

FINAL_CMD = []
final_cmd_lock = Lock()

STATE = State.LOADING

STATE_QUEUE = uniq.UniquePriorityQueue()

# the lower the number, the higher the priority
T_LOADING = (3, State.LOADING)
T_DELIVERING = (3, State.DELIVERING)
T_RETURNING = (2, State.RETURNING)
T_STOPPING = (1, State.STOPPING)
T_PANICKING = (3, State.PANICKING)

CLIENT = mqtt.Client()

def setup_procedure():
	CLIENT.on_connect = on_connect
	CLIENT.on_message = on_message
	CLIENT.connect("34.242.137.167", 1883, 60)
	CLIENT.publish("delivery_status", str(State.LOADING))
	battery_alive_thread()
	instruction_thread()
	# initialize_2nd_brick()

def on_connect(client, userdata,  flags, rc):
	client.subscribe("path_direction")
	client.subscribe("emergency_command")

def on_message(client, userdata, msg):
	if msg.topic == "path_direction":
		with chosen_path_lock:
			global CHOSEN_PATH
			CHOSEN_PATH = [Move(100,10)] #pickle.loads(msg.payload.decode())
	elif msg.topic == "emergency_command":
		string = msg.payload.decode()
		if string == "Resume":
			STATE_QUEUE.put(T_DELIVERING)
		elif string == "Stop":
			STATE_QUEUE.put(T_STOPPING)
		elif string == "Callback":
			STATE_QUEUE.put(T_RETURNING)

@thread
def instruction_thread():
	CLIENT.loop_forever()

@thread
def battery_alive_thread():
	while True:
		CLIENT.publish("battery_info_volts", payload=get_voltage())
		time.sleep(5)

def get_voltage():
    with open('/sys/class/power_supply/legoev3-battery/voltage_now') as fin:
        voltage = fin.readline()
    return voltage

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

def control_loop():
	global STATE
	while True:
		if STATE == State.LOADING:
			STATE = loading_loop() # these are going to be blocking
		elif STATE == State.DELIVERING:
			STATE = movement_loop()
		elif STATE == State.RETURNING:
			get_path()
			STATE = movement_loop() # same function as above
		elif STATE == State.STOPPING:
			STATE = stop_loop()
		elif STATE == State.PANICKING:
			STATE = panic_loop()

def get_path():
	global CHOSEN_PATH
	CHOSEN_PATH = None
	while True:
		with chosen_path_lock:
			if CHOSEN_PATH is not None:
				break

def loading_loop():
	# pool for "go-ahead" button
	get_path()
	CLIENT.publish("delivery_status", str(State.DELIVERING))
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
			CLIENT.publish("delivery_status", str(state[1]))
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
			global FINAL_CMD
			chosen_path = FINAL_CMD + CHOSEN_PATH
			FINAL_CMD = []
			move_thread = move_asynch(chosen_path, STATE)


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
def move_asynch(chosen_path, state): #all global returns will have to be passed in queues
	instruction = None
	try:
		# if state == State.RETURNING:
		# 	chosen_path = choose_path(reception = True)
		# else:
		# 	chosen_path = choose_path()
		while True:

			instruction = chosen_path.pop(0)
			success = True

			if isinstance(instruction, Move):
				success = forward(instruction.dist, instruction.tolerance)

			elif isinstance(instruction, Dump):
				pass
				#dispenser.dump(instruction.slot)

			elif isinstance(instruction, Rotate):
				if instruction.angle <= 180:
					direction = Directions.ROT_RIGHT
					angle = instruction.angle
				else:
					direction = Directions.ROT_LEFT
					angle = instruction.angle - 180
				success = rotate(angle, instruction.tolerance, direction=direction)

			elif isinstance(instruction, ToDesk):
				if instruction.is_left:
					direction = Directions.ROT_LEFT
				else:
					direction = Directions.ROT_RIGHT
				approach(direction=direction)

			elif isinstance(instruction, FromDesk):
				if instruction.is_left:
					direction = Directions.ROT_LEFT
				else:
					direction = Directions.ROT_RIGHT
				approach(direction=direction, reverse=True)

			elif isinstance(instruction, Report):
				CLIENT.publish("location_info", payload=instruction.where)

			if not success:
				print("panicking")
				STATE_QUEUE.put(T_PANICKING)
				break

			if len(chosen_path) == 0:
				if state == State.DELIVERING:
					STATE_QUEUE.put(T_RETURNING)
					break
				elif state == State.RETURNING:
					STATE_QUEUE.put(T_LOADING)
					break
		while True:
			pass

	except ThreadKiller as e:
		acknowledge(e)
		stop_motors()

		final = []

		if isinstance(instruction, Move):
			final = [Move(instruction.dist - get_odometry(), 50)]

		elif isinstance(instruction, Rotate):
			if instruction.angle <= 180:
				final = [Rotate(instruction.angle - get_odometry(rotating=True), 50)]
			else:
				final = [Rotate(instruction.angle + get_odometry(rotating=True), 50)]

		elif isinstance(instruction, FromDesk):
			get_odometry(rotating=True)
			final = [FromDesk(instruction.is_left, instruction.angle - get_odometry(rotating=True))]

		elif isinstance(instruction, ToDesk):
			get_odometry(rotating=True)
			final = [ToDesk(instruction.is_left, instruction.angle - get_odometry(rotating=True)),
			         chosen_path.pop(0), chosen_path.pop(0)] # atm it dispenses the letter even after recall

		with final_cmd_lock:
			global FINAL_CMD
			FINAL_CMD = final

		with chosen_path_lock:
			global CHOSEN_PATH
			CHOSEN_PATH = chosen_path

		sys.exit()


def panic_loop():
	CLIENT.publish("problem", "I panicked. In need of assistance. Sorry.")
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			return new_state

def stop_loop():
	# wait for further instuctons
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			return new_state


if __name__ == "__main__":
	setup_procedure()
	control_loop()
