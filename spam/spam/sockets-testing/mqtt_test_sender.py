#!/usr/bin/env python3

import paho.mqtt.client as mqtt

#This is a mock Publisher for the ev3 brick
broker_aws_host = "34.251.169.152"


client = mqtt.Client()
client.connect(broker_aws_host,1883,60)
client.publish("topic/test", "Hello world!");
# print ("Success")
client.disconnect(); #the disconnect command crashes the app
