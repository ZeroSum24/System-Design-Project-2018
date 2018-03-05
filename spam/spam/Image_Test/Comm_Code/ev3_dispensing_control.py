
#!/usr/bin/env python3

#Threading will be required to handle the camera_picture -loading variable jazz

import paho.mqtt.client as mqtt
from dispenser import dump
import json
import pickle

loading = False

def camera_picture():
	while (loading == True):
		seconds = 4
		#camera takes a picture every amount of seconds and publis
		#img = Image.open(imgpath)
		#client.publish("image_processing", payload=pickle.dumps(img))

def on_connect(client, userdata,flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("dump")
    client.subscribe("shift_slot")
    client.subscribe("finish_loading")

def on_message(client, userdata, msg):
    print("Received on topic " + msg.topic +": "+str(msg.payload.decode()))
    if msg.topic == "dump":
        slots = json.loads(msg.payload.decode())
        print(slots)
        for slot in slots:
            dump(slot)
        print('Dumped')
        client.publish("dump_confirmation", "dumped")
    elif msg.topic == "shift_slot":
        print("pass")
        # slots = json.loads(msg.payload.decode())
        # for slot in slots:
        #     dump(slot)
        #incorporate the dispensing code
	 	#has to to shift the dispensing slot after the bar code has been
    elif msg.topic == "finish_loading":
        loading = False
        #should stop the camera doing the pictures and be called when the go
		#button is pressed or all the slots have been filled

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.242.137.167", 1883, 60)

# Loop forever.
client.loop_forever()

if __name__ == "__main__":
     loading = True
     camera_picture()
