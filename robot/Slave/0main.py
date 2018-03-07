#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from dispenser import dump, stop
import json
import pickle
from subprocess import Popen, PIPE
from PIL import Image
import time
from thread_decorator import thread

current_slot = 1
slot_movement = None
loading = False

def run(*cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    stdout, stderr = proc.communicate()
    return stdout

def camera_picture():
    #Camera takes a picture using a command_line subprocess
    run("fswebcam -r 200x150 --no-banner image_sent.jpg")

    imgpath = "./image_sent.jpg"
    with open(imgpath,'rb') as img:
        data = img.read();
    client.publish("image_processing", payload=data)
    # client.publish("image_processing", payload=pickle.dumps(img))

def on_connect(client, userdata,flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("dump")
    client.subscribe("delivery_status")
    client.subscribe("go_manual")
    client.subscribe("image_result")

def on_message(client, userdata, msg):
    global slot_movement
    global current_slot
    global loading
    print("Received on topic " + msg.topic +": "+str(msg.payload.decode()))
    if msg.topic == "dump":
        slots = json.loads(msg.payload.decode())
        print(slots)
        for slot in slots:
            dump(slot)
        client.publish("dump_confirmation", "dumped")

    elif msg.topic == "delivery_status":
        if msg.payload.decode() == "State.LOADING" and loading == False:
            print("first picture")
            loading = True
            current_slot = 1
            slot_movement = stop(current_slot)
            camera_picture()
        elif msg.payload.decode() == "State.DELIVERING":
            loading = False
            slot_go_back()
            slot_movement = None

    elif msg.topic == "image_result":
        if msg.payload.decode() == "False": #test to check if its an int
            #"new_photo"
            print("qr not found - taking picture")
            camera_picture()
        else: # the qr code was identified, and the slot goes to the right place
            #"shift_slot"
            print("qr found")
            current_slot = int(msg.payload.decode())
            slot_go_back()
            print("got slot " + str(current_slot))
            if 1 <= current_slot <= 4:
                print("check passed")
                slot_movement = stop(current_slot)
                camera_picture()

    elif msg.topic == "go_manual":
        if msg.payload.decode() == "True":
            slot_go_back()

        if msg.payload.decode() == "False":
            current_slot = 1
            slot_movement = stop(current_slot)
            camera_picture()

def slot_go_back():
    global slot_movement
    try:
        if slot_movement != None:
            slot_movement.go_further()
            time.sleep(2)
            slot_movement.go_further()
            time.sleep(2)
    except StopIteration:
        print("StopIteration")

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

battery_alive_thread()

# Loop forever.
client.loop_forever()
