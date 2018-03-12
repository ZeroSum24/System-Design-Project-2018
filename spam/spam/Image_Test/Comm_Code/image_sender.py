#!/usr/bin/env python3

#This sends an image to the server to be processed by the Flask app
import paho.mqtt.client as mqtt
import sys
import pickle
from PIL import Image

broker_aws_host = "18.219.97.244"

def main(argv):

   # accepting the image argument
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgpath = argv[0]

   img = Image.open(imgpath)

   client = mqtt.Client()
   client.connect(broker_aws_host,1883,60)
   client.publish("image_processing", payload=pickle.dumps(img))

   client.loop_forever()

if __name__ == "__main__":
   main(sys.argv[1:])