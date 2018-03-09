#!/usr/bin/env python3

#This sends an image to the server to be processed by the Flask app
import paho.mqtt.client as mqtt

broker_aws_host = "34.242.137.167"

client = mqtt.Client()
client.connect(broker_aws_host,1883,60)
client.publish("battery_info_volts_2", 5);
client.disconnect()
