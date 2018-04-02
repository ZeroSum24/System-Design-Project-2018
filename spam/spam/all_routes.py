#!/usr/bin/env python3

import sys
import itertools as it
import json
import router

def flatten(gen):
    for seq in gen:
        if iter(seq):
            for item in seq:
                yield item
        else:
            yield seq

names = ["O", "P", "Q", "T", "R", "W", "V"]

def normalise_nodes(nodes):
    for slot, node in nodes:
        yield (node, [slot+1])

def extract_points(route):
    flag = False
    points = []
    for command in route:
        if flag:
            points.append(command)
            flag = False
        if command[0] == 'FromDesk':
            flag = True
    return ', '.join(map(lambda x: x[1].split('-')[0], points))

def publish_path_planning(path_direction):
    path_direction = json.dumps(path_direction)
    client.publish("path_direction", path_direction)

combinations = flatten(it.combinations(names, count)
                           for count in range(1, 6))
targets = tuple(dict(normalise_nodes(enumerate(nodes))) for nodes in combinations)
print(len(targets))
routes = [router.build_route(target) for target in targets]


import paho.mqtt.client as mqtt
route = []

def on_connect(client, *args):
    client.subscribe("request_route")
   
def on_message(client, userdata, msg):
    if msg.topic == "request_route":
        print('Here')
        publish_path_planning(router.return_from(*(msg.payload.decode().split('-'))))

client = mqtt.Client()
client.on_message = on_message
client.on_connect = on_connect
client.connect('34.242.137.167', 1883, 60)
client.loop_start()
if len(sys.argv) > 1:
    routes = routes[int(sys.argv[1]):]
l = len(routes)
for i, route in enumerate(routes):
    print('Sending route {} of {}'.format(i+1, l))
    print('Points visited: {}'.format(extract_points(route)))
    publish_path_planning(route)
    input('Press enter to continue')

if __name__ == '__main__':
    #gen()
    run()
