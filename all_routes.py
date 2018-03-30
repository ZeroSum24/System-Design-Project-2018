#!/usr/bin/env python3

import sys
import itertools as it
import json
import paho.mqtt.client as mqtt

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
    mqtt.publish("path_direction", path_direction)

def gen():
    """Generates the routes (Must be run in the same directory as router.py)"""
    import router
    combinations = flatten(it.combinations(names, count)
                           for count in range(1, 6))
    targets = tuple(dict(normalise_nodes(enumerate(nodes))) for nodes in combinations)
    print(len(targets))
    print(json.dumps([router.build_route(target) for target in targets]))

def run():
    with open('routes.txt') as f:
        routes = json.loads(f.read())
    l = len(routes)
    for i, route in enumerate(routes):
        print('Sending route {} of {}'.format(i+1, l))
        print('Points visited: {}'.format(extract_points(route)))
        publish_path_planning(route)
        input('Press enter to continue')

if __name__ == '__main__':
    #gen()
    run()
