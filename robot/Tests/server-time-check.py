import pickle
from datetime import datetime
import paho.mqtt.client as mqtt

list1 = []

thefile = open('test_output.txt', 'w')

def calculate_time_diff(time_sent):
    global list1
    now = datetime.utcnow()
    print(now)
    calculated_time = now - time_sent
    print("Time now: " + str(now))
    print("Time received: " + str(time_sent))
    print("Difference: " + str(float(calculated_time.total_seconds())))
    thefile.write("%s\n" % float(calculated_time.total_seconds()))
    list1.append(float(calculated_time.total_seconds()))
    return calculated_time

def on_message(client, userdata, msg):
    if msg.topic == "test_data_send":
        calculate_time_diff(pickle.loads(msg.payload))

def on_connect(client, userdata, flags, rc):
    client.subscribe("test_data_send")
    client.on_message = on_message

client = mqtt.Client()
client.connect("34.242.137.167", 1883, 60)
client.on_connect = on_connect
client.on_message = on_message

for i in range(10000):
    client.loop()

#
# plt.hist(list1)
# print(str(list1))
# plt.show()
