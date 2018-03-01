#!/usr/bin/env python2

#This sends an image to the server to be processed by the Flask app
import paho.mqtt.client as mqtt
import sys

broker_aws_host = "18.219.97.244"
def main(argv):

   # accepting the image argument
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgfile = argv[0]

   client = mqtt.Client()
   client.connect(broker_aws_host,1883,60)
   client.on_connect = on_connect

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.publish("topic/image_processing", imgfile);
  client.disconnect(); 

if __name__ == "__main__":
   main(sys.argv[1:])
