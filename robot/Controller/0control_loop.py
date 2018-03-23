#!/usr/bin/env python3

import sys
import time
from move import forward, rotate, approach, stop_motors, get_odometry
import State
import UniquePriorityQueue as uniq
from queue import Empty
from thread_decorator import thread, ThreadKiller, acknowledge
import Directions
import paho.mqtt.client as mqtt
import json
from collections import namedtuple
from threading import Lock
import asciiart
import imp
import speech_lib

PROFILING = False

CHOSEN_PATH = None
chosen_path_lock = Lock()

FINAL_CMD = []
final_cmd_lock = Lock()

NEXT_NODE = None
next_node_lock = Lock()

STATE = State.LOADING

STATE_RESUMED = None
state_resumed_lock = Lock()

STATE_QUEUE = uniq.UniquePriorityQueue()

DUMPED = False
dumped_lock = Lock()

SECOND_BRICK_ALIVE = False
second_brick_alive_lock =  Lock()

# the lower the number, the higher the priority
T_LOADING = (3, State.LOADING)
T_DELIVERING = (3, State.DELIVERING)
T_RETURNING = (2, State.RETURNING)
T_STOPPING = (1, State.STOPPING)
T_PANICKING = (3, State.PANICKING)

Report = namedtuple('Report', 'where')
Move = namedtuple('Move', 'dist tolerance')
Rotate = namedtuple('Rotate', 'angle tolerance')
Dump = namedtuple('Dump', 'slots')
ToDesk = namedtuple('ToDesk', 'is_left angle')
FromDesk = namedtuple('FromDesk', 'is_left angle tolerance')

CLIENT = mqtt.Client()

with open('ip.conf') as f:
	IP = imp.load_source('ip', '', f).ip

def setup_procedure():
	CLIENT.on_connect = on_connect
	CLIENT.on_message = on_message
	# TODO do IO exceptions
	CLIENT.connect(IP, 1883, 60)
	instruction_thread()
	while True:
		with second_brick_alive_lock:
			if SECOND_BRICK_ALIVE == True:
				break
		#print("spin")
		time.sleep(2)
	battery_alive_thread()
	CLIENT.publish("delivery_status", str(State.LOADING))

def on_connect(client, userdata, flags, rc):
	print(asciiart.spam())
	client.subscribe("path_direction")
	client.subscribe("emergency_command")
	client.subscribe("dump_confirmation")
	client.subscribe("battery_info_volts_2")
	client.subscribe("ascii_art")

def on_message(client, userdata, msg):
	global DUMPED, SECOND_BRICK_ALIVE, CHOSEN_PATH
	if msg.topic == "path_direction":
		with chosen_path_lock:
			CHOSEN_PATH = generate_named_tuples(json.loads(msg.payload.decode()))
	elif msg.topic == "emergency_command":
		string = msg.payload.decode()
		if string == "Resume":
			with state_resumed_lock:
				STATE_QUEUE.put((2, STATE_RESUMED))
		elif string == "Stop":
			STATE_QUEUE.put(T_STOPPING)
		elif string == "Callback":
			STATE_QUEUE.put(T_RETURNING)
	elif msg.topic == "dump_confirmation":
		#print('Got Confirmation')
		with dumped_lock:
			#print('Set Flag')
			DUMPED = True
	elif SECOND_BRICK_ALIVE == False and msg.topic == "battery_info_volts_2":
		#print("second brick alive")
		SECOND_BRICK_ALIVE = True

	elif msg.topic == "ascii_art":
		global asciiart
		asciiart = msg.payload.decode()
		print (asciiart)

def generate_named_tuples(lst):
	new_list = []
	for listee in lst:
		if listee[0] == "Report":
			new_list.append(Report(listee[1]))
		elif listee[0] == "Move":
			new_list.append(Move(listee[1], listee[2]))
		elif listee[0] == "Rotate":
			new_list.append(Rotate(listee[1], listee[2]))
		elif listee[0] == "Dump":
			new_list.append(Dump(listee[1]))
		elif listee[0] == "ToDesk":
			new_list.append(ToDesk(listee[1], listee[2]))
		elif listee[0] == "FromDesk":
			new_list.append(FromDesk(listee[1], listee[2], listee[3]))
	return new_list

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

def control_loop():
	global STATE
	while True:
		#print(STATE)
		if STATE == State.LOADING:
			STATE = loading_loop() # these are going to be blocking
		elif STATE == State.DELIVERING:
			STATE = movement_loop()
		elif STATE == State.RETURNING:
			get_path(returning=True)
			STATE = movement_loop() # same function as above
			if PROFILING:
				sys.exit()
		elif STATE == State.STOPPING:
			STATE = stop_loop()
		elif STATE == State.PANICKING:
			STATE = panic_loop()

def get_path(returning=False):
	#print(returning)
	global CHOSEN_PATH
	with chosen_path_lock:
		CHOSEN_PATH = None
	if returning:
		with next_node_lock:
			CLIENT.publish("request_route", NEXT_NODE)
	while True:
		with chosen_path_lock:
			if CHOSEN_PATH is not None:
				break

def loading_loop():
	# pool for "go-ahead" button
	with next_node_lock:
		global NEXT_NODE
		NEXT_NODE = None
	with STATE_QUEUE.mutex:
		STATE_QUEUE.clear()
	get_path()
	CLIENT.publish("delivery_status", str(State.DELIVERING))
	return State.DELIVERING

def check_state(current_state):
	try:
		state = STATE_QUEUE.get_nowait()
	except Empty:
		return None
	else:
		#print("got {}".format(state))
		if state[1] != current_state:
			with STATE_QUEUE.mutex:
				STATE_QUEUE.clear()
			CLIENT.publish("delivery_status", str(state[1]))
			return state[1]
		else:
			return None

def movement_loop():
	moving_flag = False
	move_thread = None
	with STATE_QUEUE.mutex:
		STATE_QUEUE.clear()
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			if move_thread is not None:
				move_thread.stop()
			return new_state

		if not moving_flag:
			moving_flag = True
			global FINAL_CMD
			with final_cmd_lock, chosen_path_lock:
				chosen_path = FINAL_CMD + CHOSEN_PATH
				FINAL_CMD = []
			with state_resumed_lock:
				global STATE_RESUMED
				STATE_RESUMED = STATE
			move_thread = move_asynch(chosen_path, STATE)

@thread
def move_asynch(chosen_path, state): #all global returns will have to be passed in queues
	global DUMPED, NEXT_NODE
	instruction = None
	try:
		while True:

			instruction = chosen_path.pop(0)
			success = True

			if isinstance(instruction, Move):
				#print("moving")
				success = forward(instruction.dist, tolerance = instruction.tolerance)

			elif isinstance(instruction, Dump):
				if not PROFILING:
					CLIENT.publish("dump", json.dumps(instruction.slots))
					while True:
						with dumped_lock:
							if DUMPED:
								DUMPED = False
								break

			elif isinstance(instruction, Rotate):
				#print("rotating")
				if instruction.angle <= 180:
					direction = Directions.ROT_RIGHT
					angle = instruction.angle
				else:
					direction = Directions.ROT_LEFT
					angle = instruction.angle - 180
				success = rotate(angle, tolerance = instruction.tolerance, direction = direction)

			elif isinstance(instruction, ToDesk):
				#print("approaching desk")
				angle = instruction.angle
				if instruction.is_left:
					direction = Directions.ROT_LEFT
				else:
					direction = Directions.ROT_RIGHT
				approach(angle=angle, direction=direction)

			elif isinstance(instruction, FromDesk):
				#print("leaving desk")
				angle = instruction.angle
				if instruction.is_left:
					direction = Directions.ROT_LEFT
				else:
					direction = Directions.ROT_RIGHT
				success = approach(angle=angle, tolerance=instruction.tolerance, direction=direction, reverse=True)

			elif isinstance(instruction, Report):
				#print("reporting")
				CLIENT.publish("location_info", payload=instruction.where)

			if not success:
				#print("panicking")
				STATE_QUEUE.put(T_PANICKING)
				break

			if len(chosen_path) == 0:
				if state == State.DELIVERING:
					#print("Returning")
					STATE_QUEUE.put(T_RETURNING)
					#print(STATE_QUEUE)
					break
				elif state == State.RETURNING:
					#print("Loading")
					STATE_QUEUE.put(T_LOADING)
					break

		# last reported location for return
		with next_node_lock:
			if isinstance(instruction, Report):
				NEXT_NODE = instruction.where
		#print(NEXT_NODE)
		# TODO right now the code spins here forever after executing the movement
		# commands - does not need to
		while True:
			pass

	except ThreadKiller as e:
		acknowledge(e)
		stop_motors()

		final = []

		if isinstance(instruction, Move):
			dist = instruction.dist - get_odometry()
			if dist <= 10:
				final = [Move(10, 100)]
			else:
				final = [Move(dist, 50)]
			if chosen_path and isinstance(chosen_path[0], Rotate):
				final.append(chosen_path.pop(0))

		elif isinstance(instruction, Dump):
			while True:
				with dumped_lock:
					if DUMPED:
						DUMPED = False
						break

		elif isinstance(instruction, Rotate):
			if instruction.angle <= 180:
				angle = instruction.angle - get_odometry(rotating=True)
				if angle <= 10:
					final = [Rotate(10, 100)]
				else:
					final = [Rotate(angle, 50)]
			else:
				angle = instruction.angle + get_odometry(rotating=True)
				if angle >= 350:
					final = [Rotate(350, 100)]
				else:
					final = [Rotate(angle, 50)]

		elif isinstance(instruction, FromDesk):
			get_odometry(rotating=True)
			final = [FromDesk(instruction.is_left, instruction.angle - get_odometry(rotating=True), 50)]

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

		with next_node_lock:
			for instructione in chosen_path:
				if isinstance(instructione, Report):
					NEXT_NODE = instructione.where
					break

		sys.exit()

def panic_loop():
	with next_node_lock:
		CLIENT.publish("problem", "I panicked next to {}. In need of assistance. Sorry.".format(NEXT_NODE))
	with final_cmd_lock:
		global FINAL_CMD
		FINAL_CMD = []
	# while True:
	# 	new_state = check_state(STATE)
	# 	if new_state != None:
	# 		return new_state
	CLIENT.publish("delivery_status", str(State.LOADING))
	return State.LOADING

def stop_loop():
	# wait for further instuctons
	while True:
		new_state = check_state(STATE)
		if new_state != None:
			return new_state

def main():
	setup_procedure()
	control_loop()

if __name__ == "__main__":
	main()
