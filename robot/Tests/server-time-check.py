import pickle
from datetime import datetime
import paho.mqtt.client as mqtt

CLIENT = mqtt.Client()
CLIENT.connect("34.242.137.167", 1883, 60)
CLIENT.subscribe("test_data_send")

def calculate_time_diff(time_sent):
    now = datetime.datetime.utcnow()
    calculated_time = now - pickle.loads(time_sent)
    print(":)")
    return calculated_time


def on_message(client, userdata, msg):
    print("if statement")
    if msg.topic == "test_data_send":
        calculate_time_diff(msg.payload.decode)

for i in range(999999999):
    CLIENT.on_message = on_message
