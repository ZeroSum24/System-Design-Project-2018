#!/usr/bin/env python3

#This sends an image to the server to be processed by the Flask app
import paho.mqtt.client as mqtt

broker_aws_host = "18.219.97.244"

client = mqtt.Client()
client.connect(broker_aws_host,1883,60)
client.publish("topic/image_processing", "Hello world!");
client.disconnect()
