#!/usr/bin/env python3

#This is the MQTT handler for both sending and receiving data

import paho.mqtt.client as mqtt


broker_aws_host = "34.251.169.152"
path_directions = []

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.subscribe("topic/emergency_commands")
  client.subscribe("topic/path_directions")
  client.publish("topic/connection_established", payload=True)

def on_message(client, userdata, msg):
  if msg.topic == "emergency_commands":
      if msg.decode == "stop":
          print ("Stop Command")
          return msg.decode
      if msg.decode == "recall":
          print ("Recall Command")
          return msg.decode
      if msg.decode == "continue":
          print ("Continue Command")
          return msg.decode
      if msg.decode == "restart":
          print ("Restart Command")
          return msg.decode
  elif msg.topic == "path_directions":
      path_directions = msg.decode()


def report_location(location_info):
    client.publish("topic/location", location_info)
    return True

def report_battery_life(battery_info):
    client.publish("topic/battery", battery_info)
    #find a way to pull the ev3 bricks current voltage level
    # from the brick (may tie in with the graph data)
    pass


client = mqtt.Client()
client.connect(broker_aws_host,1883,60)

client.on_connect = on_connect
client.on_message = on_message
