
import paho.mqtt.client as mqtt

#This is a mock Publisher for the ev3 brick
broker_aws_host = "34.242.137.167"

dump_list = [1,2,3,4]

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.publish("topic/dump", dump_list);
  client.disconnect(); #the disconnect command crashes the app

client = mqtt.Client()

client.connect(broker_aws_host,1883,60)

client.on_connect = on_connect

