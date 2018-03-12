#!/usr/bin/env python3

import paho.mqtt.client as mqtt
# from dispenser import dump, stop
import json
import pickle
from subprocess import Popen, PIPE
from PIL import Image

current_slot = 0

def run(*cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    stdout, stderr = proc.communicate()
    return stdout

def camera_picture():
    #Camera takes a picture using a command_line subprocess
    run("fswebcam -r 1280x720 image_sent.jpg")
    img = Image.open("./image_sent.jpg")
    client.publish("image_processing", payload=pickle.dumps(img))

def on_connect(client, userdata,flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("dump")
    client.subscribe("delivery_status")
    client.subscribe("new_photo")
    client.subscribe("shift_slot")

def on_message(client, userdata, msg):
    print("Received on topic " + msg.topic +": "+str(msg.payload.decode()))
    if msg.topic == "dump":
        slots = json.loads(msg.payload.decode())
        print(slots)
        for slot in slots:
            dump(slot)
        print('Dumped')
        client.publish("dump_confirmation", "dumped")
    elif msg.topic == "delivery_status" and str(msg.payload.decode()) == "State.LOADING":
        print("first letter")
        global
        camera_picture()
        #dispenser.stop(1)
    elif msg.topic == "new_photo":
        camera_picture()
    elif msg.topic == "shift_slot":
        global current_slot
        current_slot = int(msg.payload.decode())
        #incorporate the dispensing code
        #dispenser.stop(current_slot)
        #has to to shift the dispensing slot after the bar code has been
        camera_picture()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.242.137.167", 1883, 60)

# Loop forever.
client.loop_forever()
