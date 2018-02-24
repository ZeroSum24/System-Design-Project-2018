#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from dispenser import dump
import json

def on_connect(client, userdata,flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("dump")

def on_message(client, userdata, msg):
    print("Received on topic " + msg.topic +": "+str(msg.payload.decode()))
    if msg.topic == 'dump':
        slots = json.loads(msg.payload.decode())
        print(slots)
        for slot in slots:
            dump(slot)
        print('Dumped')
        client.publish("dump_confirmation", "dumped")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.242.137.167", 1883, 60)

# Loop forever.
client.loop_forever()
