
import paho.mqtt.client as mqtt

#This is a mock Publisher for the ev3 brick
broker_aws_host = "34.251.169.152"

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.publish("topic/test", "Hello world!");
  client.disconnect(); #the disconnect command crashes the app

client = mqtt.Client()

client.connect(broker_aws_host,1883,60)

client.on_connect = on_connect
# print ("Success")
