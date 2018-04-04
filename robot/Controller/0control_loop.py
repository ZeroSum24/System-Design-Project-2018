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

# If true changes some of the behavior of the control loop to make profiling
# easier
PROFILING = False

# The route the robot is currently following
CHOSEN_PATH = None
chosen_path_lock = Lock()

# Incase of interuption this will contain the last instruction the robot was
# executing on resume.
FINAL_CMD = []
final_cmd_lock = Lock()

# The node we are due to reach next. Used during when the robot attempts to
# return to the reception (either due to a callback or by finishing its
# deliveries).
NEXT_NODE = None
next_node_lock = Lock()

# The current state
STATE = State.LOADING

# In case of an iterupt during motion this will hold either State.DELIVERING or
# State.RETURNING, the two are otherwise indistinguisable on resume.
STATE_RESUMED = None
state_resumed_lock = Lock()

# When the robot or the server wish to change the robots state they push values
# here, the robot gets new state with respect to the ordering given
# below. Duplicate states in the queue are disallowed.
STATE_QUEUE = uniq.UniquePriorityQueue()

# Required to allow the second brick to signal that it has finished dumping via
# MQTT
DUMPED = False
dumped_lock = Lock()

# Required so we don't do anything before the dumper is ready
SECOND_BRICK_ALIVE = False
second_brick_alive_lock = Lock()

# The lower the number, the higher the priority, high priority states can
# preempt low priority states regardless of when they were registered in the
# queue
T_LOADING = (3, State.LOADING)
T_DELIVERING = (3, State.DELIVERING)
T_RETURNING = (2, State.RETURNING)
T_STOPPING = (1, State.STOPPING)
T_PANICKING = (3, State.PANICKING)

# Commands come in as JSON and are translated into named tuples
Report = namedtuple('Report', 'where')
Move = namedtuple('Move', 'dist tolerance')
Rotate = namedtuple('Rotate', 'angle tolerance')
Dump = namedtuple('Dump', 'slots')
ToDesk = namedtuple('ToDesk', 'is_left angle')
FromDesk = namedtuple('FromDesk', 'is_left angle tolerance')

CLIENT = mqtt.Client()

# Get the server's ip address from a config file
with open('ip.conf') as f:
    IP = imp.load_source('ip', '', f).ip

def setup_procedure():
    # Setup MQTT
    CLIENT.on_connect = on_connect
    CLIENT.on_message = on_message
    # TODO do IO exceptions
    CLIENT.connect(IP, 1883, 60)
    CLIENT.loop_start()#instruction_thread()
    # Spin until we recive notification that the second brick is online
    while True:
        with second_brick_alive_lock:
            if SECOND_BRICK_ALIVE == True:
                break
        #print("spin")
        time.sleep(2)
    # Start sending our own battery notifications
    battery_alive_thread()
    # And notify the server we are ready to load
    CLIENT.publish("delivery_status", str(State.LOADING))

def on_connect(client, userdata, flags, rc):
    client.subscribe("path_direction")
    client.subscribe("emergency_command")
    client.subscribe("dump_confirmation")
    client.subscribe("battery_info_volts_2")
    client.subscribe("ascii_art_slave")

def on_message(client, userdata, msg):
    global DUMPED, SECOND_BRICK_ALIVE, CHOSEN_PATH
    if msg.topic == "path_direction":
        # When a path comes in parse it and store it
        with chosen_path_lock:
            CHOSEN_PATH = generate_named_tuples(json.loads(msg.payload.decode()))
    elif msg.topic == "emergency_command":
        # When an emergency command comes in push the relavent state (the
        # priority queue handles the urgency of different commands)
        string = msg.payload.decode()
        if string == "Resume":
            with state_resumed_lock:
                STATE_QUEUE.put((2, STATE_RESUMED))
        elif string == "Stop":
            STATE_QUEUE.put(T_STOPPING)
        elif string == "Callback":
            STATE_QUEUE.put(T_RETURNING)
    elif msg.topic == "dump_confirmation":
        # When the second brick says it dumped set the flag (Will be handled by
        # move_asych)
        #print('Got Confirmation')
        with dumped_lock:
            #print('Set Flag')
            DUMPED = True
    elif SECOND_BRICK_ALIVE == False and msg.topic == "battery_info_volts_2":
        # For above
        #print("second brick alive")
        with second_brick_alive_lock:
            SECOND_BRICK_ALIVE = True
    elif msg.topic == "ascii_art_slave":
        # Allows the server to send ascii art to display on screen
        if msg.payload.decode() == "full":
            asciiart.full()

def generate_named_tuples(lst):
    # Type of command is the first item of the sublist, the rest are arguments
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

# @thread
# def instruction_thread():
#     CLIENT.loop_forever()

@thread
def battery_alive_thread():
    # Send the battery voltage level every 5 seconds
    while True:
        CLIENT.publish("battery_info_volts", payload=get_voltage())
        time.sleep(5)

def get_voltage():
    # Read the battery voltage
    with open('/sys/class/power_supply/legoev3-battery/voltage_now') as fin:
        voltage = fin.readline()
    return voltage

def control_loop():
    # Overarching state machine of the robot. Each function blocks and returns
    # the new state when it finished. Due to support for interrupts the state
    # retuned from movement_loop is non-deterministic
    global STATE
    while True:
        #print(STATE)
        if STATE == State.LOADING:
            # When we hit loading display the logo
            asciiart.spam()
            STATE = loading_loop()
        elif STATE == State.DELIVERING:
            # When we are deliviering print the delivery message and start
            # moving
            asciiart.delivering_mail()
            STATE = movement_loop()
        elif STATE == State.RETURNING:
            # When we are returning print that message, request a return route
            # from the server and start moving
            asciiart.returning()
            get_path(returning=True)
            STATE = movement_loop()
            if PROFILING:
                # This is required for profiling or the main thread never stops
                sys.exit()
        elif STATE == State.STOPPING:
            # When stopped just wait for new instructions
            STATE = stop_loop()
        elif STATE == State.PANICKING:
            # When panicking notify reception then wait for new instructions
            STATE = panic_loop()

def get_path(returning=False):
    #print(returning)
    global CHOSEN_PATH
    # Clear the old path
    with chosen_path_lock:
        CHOSEN_PATH = None
    if returning:
        # If we are returning tell the server where we are (Or will be in the
        # case of a callback)
        with next_node_lock:
            CLIENT.publish("request_route", NEXT_NODE)
    # In either case wait for a path to be sent
    while True:
        with chosen_path_lock:
            if CHOSEN_PATH is not None:
                break

def loading_loop():
    # pool for "go-ahead" button
    # Clear NEXT_NODE and any states that haven't been addressed
    with next_node_lock:
        global NEXT_NODE
        NEXT_NODE = None
    with STATE_QUEUE.mutex:
        STATE_QUEUE.clear()
    # Wait for a route
    get_path()
    # Notify the server that we are delivering
    CLIENT.publish("delivery_status", str(State.DELIVERING))
    # Also take that transition in the state machine
    return State.DELIVERING

def check_state(current_state):
    # Used to poll for new state from the server and move_asynch
    try:
        # Attempt to get a new state
        state = STATE_QUEUE.get_nowait()
    except Empty:
        # If the queue is empty abort
        return None
    else:
        #print("got {}".format(state))
        if state[1] != current_state:
            # Otherwise clear the rest of the waiting states
            with STATE_QUEUE.mutex:
                STATE_QUEUE.clear()
            # Publish and return the new state
            CLIENT.publish("delivery_status", str(state[1]))
            return state[1]
        else:
            # If the state retrieved is the same as the current state abort
            return None

def movement_loop():
    # Clear any waiting states prior to moving
    with STATE_QUEUE.mutex:
        STATE_QUEUE.clear()

    global FINAL_CMD
    with final_cmd_lock, chosen_path_lock:
        # Prepend the last command from the last movement loop to the current
        # path (it is non-empty when the robot was interupted)
        chosen_path = FINAL_CMD + CHOSEN_PATH
        FINAL_CMD = []

    # Save the state we are currently in incase of intruption
    with state_resumed_lock:
        global STATE_RESUMED
        STATE_RESUMED = STATE

    # Spawn a thread to to the movement
    move_thread = move_asynch(chosen_path, STATE)

    while True:
        # Wait a bit (Kicks this thread off the interpreter to allow the
        # move_asynch thread to have more cpu time)
        time.sleep(0.3)
        # Poll for new state
        new_state = check_state(STATE)
        # If we ever get something kill the thread and return it up to the state
        # machine
        if new_state != None:
            # This does nothing if the thread died of its own accord
            move_thread.stop()
            return new_state

@thread
def move_asynch(chosen_path, state):
    global DUMPED, NEXT_NODE
    instruction = None
    # Calling stop on this thread throws ThreadKiller at the current point of
    # execution, wrapping all of the logic in a try catch allows for cleanup and
    # prevents the stack trace.
    try:
        while True:
            # Get the next instruction
            instruction = chosen_path.pop(0)
            success = True

            # Dispatch to the relavent functions depending on the command
            if isinstance(instruction, Move):
                #print("moving")
                success = forward(instruction.dist, tolerance = instruction.tolerance)

            elif isinstance(instruction, Dump):
                # Communication between the two bricks was turned off during
                # profiling
                if not PROFILING:
                    # Instruct the second brick to dump
                    CLIENT.publish("dump", json.dumps(instruction.slots))
                    # Spin until it replies
                    while True:
                        with dumped_lock:
                            if DUMPED:
                                DUMPED = False
                                break

            elif isinstance(instruction, Rotate):
                #print("rotating")
                # The route planner always generates instructions telling the
                # robot to turn right, this adapts to turn left when that is
                # more efficient
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
                # This function unconditionally turns 90 degrees and so can't
                # fail
                approach(angle=angle, direction=direction)

            elif isinstance(instruction, FromDesk):
                #print("leaving desk")
                angle = instruction.angle
                if instruction.is_left:
                    direction = Directions.ROT_LEFT
                else:
                    direction = Directions.ROT_RIGHT
                # On the way back however it searches for a line so can
                success = approach(angle=angle, tolerance=instruction.tolerance, direction=direction, reverse=True)

            elif isinstance(instruction, Report):
                #print("reporting")
                CLIENT.publish("location_info", payload=instruction.where)

            # If an instruction failed panic
            if not success:
                #print("panicking")
                STATE_QUEUE.put(T_PANICKING)
                break

            # If we ran out of instructions without panicking make a transition
            # depending on what state we are currently in
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

        # Last reported location for return
        with next_node_lock:
            if isinstance(instruction, Report):
                NEXT_NODE = instruction.where
        #print(NEXT_NODE)
        # TODO right now the code spins here forever after executing the movement
        # commands - does not need to
        while True:
            pass

    except ThreadKiller as e:
        # There is a certain amount of unreliability in the method used to kill
        # threads (See thread_decorator.py) so the code keeps sending exceptions
        # until the thread dies or calls acknowledge. After a call to
        # acklowledge the thread is allowed as much time as it needs to cleanup.
        acknowledge(e)
        stop_motors()

        final = []

        # Resolve the various instructions where we could have been interupted
        if isinstance(instruction, Move):
            # Inside move figure out how far we still need to go and store that
            # for next time. (If it is too small search for the junction
            # anywhere between 0 and 20)
            dist = instruction.dist - get_odometry()
            if dist <= 20:
                final = [Move(20, 100)]
            else:
                final = [Move(dist, 50)]
            # If there is a rotate next also take that
            if chosen_path and isinstance(chosen_path[0], Rotate):
                final.append(chosen_path.pop(0))

        elif isinstance(instruction, Dump):
            # If it's a dump assume we've managed to send the message (It's
            # highly unlikley we will be interupted exactly between poping a
            # Dump and sending the message). Wait for the confirmation before
            # finishing
            while True:
                with dumped_lock:
                    if DUMPED:
                        DUMPED = False
                        break

        elif isinstance(instruction, Rotate):
            # Rotate follows the same theory as move while also dealing with
            # whether we were turning left or right
            if instruction.angle <= 180:
                angle = instruction.angle - get_odometry(rotating=True)
                if angle <= 20:
                    final = [Rotate(20, 100)]
                else:
                    final = [Rotate(angle, 50)]
            else:
                angle = instruction.angle + get_odometry(rotating=True)
                if angle >= 340:
                    final = [Rotate(340, 100)]
                else:
                    final = [Rotate(angle, 50)]

        elif isinstance(instruction, FromDesk):
            # Same as move and rotate
            final = [FromDesk(instruction.is_left, instruction.angle - get_odometry(rotating=True), 50)]

        elif isinstance(instruction, ToDesk):
            # Here also dispense the letter given we are at a desk
            final = [ToDesk(instruction.is_left, instruction.angle - get_odometry(rotating=True)),
                     chosen_path.pop(0), chosen_path.pop(0)] # atm it dispenses the letter even after recall

        # Save the generated command
        with final_cmd_lock:
            global FINAL_CMD
            FINAL_CMD = final

        # Save the current path (Will be used for resume)
        with chosen_path_lock:
            global CHOSEN_PATH
            CHOSEN_PATH = chosen_path

        # Store the node we are going to reach next (Will be used for callback)
        with next_node_lock:
            for instructione in chosen_path:
                if isinstance(instructione, Report):
                    NEXT_NODE = instructione.where
                    break

        sys.exit()

def panic_loop():
    # Notify reception that we panicked and give an approximate location
    with next_node_lock:
        speech_lib.panicking()
        CLIENT.publish("problem", "I panicked next to {}. In need of assistance. Sorry.".format(NEXT_NODE))

    # Clear the final command (If we restart we will be back at reception)
    with final_cmd_lock:
        global FINAL_CMD
        FINAL_CMD = []
    # while True:
    #     new_state = check_state(STATE)
    #     if new_state != None:
    #         return new_state
    # For testing and demonstration drop immedatly into loading
    CLIENT.publish("delivery_status", str(State.LOADING))
    return State.LOADING

def stop_loop():
    # Wait for further instructions
    while True:
        new_state = check_state(STATE)
        if new_state != None:
            return new_state

def main():
    setup_procedure()
    control_loop()

if __name__ == "__main__":
    main()
