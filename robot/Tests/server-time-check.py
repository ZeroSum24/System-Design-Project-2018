import pickle
from time import sleep
from datetime import datetime, timestamp
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt

list1 = []

def calculate_time_diff(time_sent):
    global list1
    now = datetime.utcnow()
    calculated_time = now - time_sent
    print("Time now: " + str(now))
    print("Time recieved: " + str(time_sent))
    print("Difference: " + str(float(calculated_time.timestamp())))
    list1.append(float(calculated_time.timestamp()))
    return calculated_time

def on_message(client, userdata, msg):
    if msg.topic == "test_data_send":
        calculate_time_diff(pickle.loads(msg.payload))

def on_connect(client, userdata, flags, rc):
    client.subscribe("test_data_send")
    client.on_message=on_message

client = mqtt.Client()
client.connect("34.242.137.167", 1883, 60)
client.on_connect = on_connect
client.on_message = on_message

for i in range(45):
    client.loop()

plt.hist(list1)
plt.show()