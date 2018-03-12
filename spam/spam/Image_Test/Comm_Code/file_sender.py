#!/usr/bin/env python3

# Potential method to reduce amount of data sent to the server per-photo
import paho.mqtt.client as mqtt
import sys

broker_aws_host = "34.242.137.167"

def main(argv):

   # accepting the image argument
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgpath = argv[0]

   with open(imgpath,'rb') as img:
       data = img.read();

   client = mqtt.Client()
   client.connect(broker_aws_host,1883,60)
   client.publish("delivery_status", "State.LOADING")
   client.publish("image_processing", payload=data) #unlikely need to pickle

   client.loop_forever()

if __name__ == "__main__":
   main(sys.argv[1:])
