#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from dispenser import dump, stop
import json
import pickle
from subprocess import Popen, PIPE
from PIL import Image
import time

current_slot = 1
slot_movement = None
loading = False

def run(*cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    stdout, stderr = proc.communicate()
    return stdout

def camera_picture():
    #Camera takes a picture using a command_line subprocess
    run("fswebcam -r 800x600 image_sent.jpg")
    img = Image.open("./image_sent.jpg")
    # with open("./image_sent.jpg", 'r+') as f:
    #     img = f.read()
    client.publish("image_processing", payload=pickle.dumps(img))

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
            try:
                slot_movement.go_further()
                slot_movement.go_further()
            except StopIteration:
                pass

    elif msg.topic == "image_result":
        if msg.payload.decode() == "False": #test to check if its an int
            #"new_photo"
            print("qr not found - taking picutre")
            camera_picture()
        else: # the qr code was identified, and the slot goes to the right place
            #"shift_slot"
            print("qr found")
            current_slot = int(msg.payload.decode())
            slot_movement.go_further()
            time.sleep(2)
            slot_movement.go_further()
            slot_movement = stop(current_slot)
            camera_picture()

    elif msg.topic == "go_manual":
        if msg.payload.decode() == "True":
            slot_movement.go_further()
            time.sleep(2)
            slot_movement.go_further()

        if msg.payload.decode() == "False":
            current_slot = 1
            slot_movement = stop(current_slot)
            camera_picture()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.242.137.167", 1883, 60)

# Loop forever.
client.loop_forever()
