#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from dispenser import dump, stop, reset_dumper
import json
from subprocess import Popen, PIPE
import time
from thread_decorator import thread
import os

current_slot = 1
slot_movement = None
loading = False
in_automatic = True

def run(*cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True).wait()
    stdout, _ = proc.communicate()
    return stdout

# def _camera_picture():
#     #Camera takes a picture using a command_line subprocess
#     run("fswebcam -r 200x150 --no-banner image_sent.jpg")
#
#     imgpath = "./image_sent.jpg"
#     with open(imgpath,'rb') as img:
#         data = img.read();
#     client.publish("image_processing", payload=data)
#     # client.publish("image_processing", payload=pickle.dumps(img))

def camera_picture():
    os.system('./take_photo.sh')
    imgpath = "./image_sent.jpg"
    with open(imgpath,'rb') as img:
        data = img.read();
    client.publish("image_processing", payload=data)

def on_connect(client, userdata,flags, rc):
    # print("Connected with result code "+str(rc))
    client.subscribe("dump")
    client.subscribe("delivery_status")
    client.subscribe("go_manual")
    client.subscribe("image_result")

def on_message(client, userdata, msg):
    global slot_movement, current_slot, loading, in_automatic
    # print("Received on topic " + msg.topic +": "+str(msg.payload.decode()))
    if msg.topic == "dump":
        slots = json.loads(msg.payload.decode())
        # print(slots)
        for slot in slots:
            dump(slot)
        client.publish("dump_confirmation", "dumped")

    elif msg.topic == "delivery_status":
        if msg.payload.decode() == "State.LOADING" and loading == False:
            # print("first picture")
            loading = True
            current_slot = 1
            # print("setting up on loading")
            slot_movement = stop(current_slot)
            # print("done setting up on loading")
            camera_picture()
        elif msg.payload.decode() == "State.DELIVERING":
            loading = False
            # print("going back on delivering")
            slot_go_back(wait = False)
            # print("done going back on delivering")
            slot_movement = None

    elif msg.topic == "image_result" and in_automatic == True:
        if msg.payload.decode() == "False": #test to check if its an int
            #"new_photo"
            # print("qr not found - taking picture")
            camera_picture()
        else: # the qr code was identified, and the slot goes to the right place
            #"shift_slot"
            # print("qr found")
            current_slot = int(msg.payload.decode())
            # print("going back between pictures")
            slot_go_back()
            # print("done going back")
            if 1 <= current_slot <= 4:
                # print("going to slot " + str(current_slot))
                slot_movement = stop(current_slot)
                # print("done going to slot")
                camera_picture()

    elif msg.topic == "go_manual":
        if msg.payload.decode() == "True" and in_automatic == True:
            in_automatic = False
            slot_go_back()

        if msg.payload.decode() == "False" and in_automatic == False:
            in_automatic = True
            reset_dumper()
            current_slot = 1
            slot_movement = stop(current_slot)
            camera_picture()

def slot_go_back(wait = True):
    global slot_movement
    try:
        if slot_movement != None:
            slot_movement.go_further()
            if wait:
                time.sleep(2)
            slot_movement.go_further()
    except StopIteration:
        # print("StopIteration")
        pass

@thread
def battery_alive_thread():
	while True:
		client.publish("battery_info_volts_2", payload=get_voltage())
		time.sleep(5)

def get_voltage():
    with open('/sys/class/power_supply/legoev3-battery/voltage_now') as fin:
        voltage = fin.readline()
    return voltage

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.242.137.167", 1883, 60)

reset_dumper()
battery_alive_thread()
# Loop forever.
client.loop_forever()
