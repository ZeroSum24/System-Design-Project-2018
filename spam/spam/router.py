#!/usr/bin/env python3

# Allows router to be imported outside of flask
try:
    from spam.graph import Edge, Graph
    from spam.Commands import *
except ImportError:
    from graph import Edge, Graph
    from Commands import *
import itertools
from os import environ

_MAP = {'S' : {'A' : (5, 90, 270),
               'C' : (10, 0, 180)},
        'A' : {'B' : (5, 90, 270),
               'K' : (0, 0, 180)},
        'B' : {'D' : (10, 0, 180)},
        'C' : {'E' : (10, 0, 180),
               'J' : (0, 90, 270)},
        'D' : {'G' : (10, 0, 180),
               'I' : (0, 270, 90)},
        'E' : {'F' : (5, 90, 270)},
        'F' : {'G' : (5, 90, 270),
               'H' : (0, 180, 0)}}

def _build_graph():
    edges = []
    for start in mapp:
        for end in mapp[start]:
            edges.append(Edge(start, end, _MAP[start][end][0]))
    return Graph(edges)

# From the itertools docs
def _pairwise(iterable):
    # Produce two iterators pointing to the start of the iterable
    a, b = itertools.tee(iterable)
    # Advance the second one by 1 place (Returns None if the iterable only has
    # one element)
    next(b, None)
    # Zip them together
    return zip(a, b)

def _path_dist(path):
    dist = 0
    for pair in _pairwise(path):
        dist += _get_edge_stats(*pair)[0]
    return dist

def _get_edge_stats(start, end):
    try:
        dist, src_ang, dest_ang = _MAP[start][end]
    except KeyError:
        dist, dest_ang, src_ang = _MAP[end][start]
    return dist, src_ang, dest_ang

def build_route(points):
    # Avoid mutating the argument
    points = dict(points)
    # Algorithm generates several subroutes that must then be unified
    routes = []
    # Start symbol
    start = 'S'
    # Always start facing 0 degrees
    facing = 0
    while points:
        # Pair start with every point (Zip on a dict uses the keys)
        pairs = zip(start * len(points), points)
        # Plot the route for each pair and select the minimum path using
        # _path_dist as a metric
        nodes = min((_GRAPH.route(*pair) for pair in pairs), key=_path_dist)
        # This path will end at a desk, the node before that is the point on the
        # line that the robot will end up at after it's finished dumping
        start = nodes[-2]
        desk = nodes[-1]
        route = []
        # For each edge in the route (Not counting the desk)
        for src, dest in _pairwise(nodes[:-1]):
            # Get the required statistics
            dist, src_ang, dest_ang = _get_edge_stats(src, dest)
            # Report reaching the source node
            route.append(Report(src))
            # Rotate to the correct angle to exit relative to where we are
            # currently facing
            route.append(Rotate((src_ang-facing)%360, 0.3))
            # Calculate the direction we will be facing upon reaching the next
            # node
            facing = (dest_ang + 180) % 360
            # Move move the required distance down the line
            route.append(Move(dist, 0.3))
        # At the end of the route dump the required slots
        # Figure out which direction to dump in
        # Only src_ang is relevant here, the others are just for homogeny
        dist, src_ang, dest_ang = _get_edge_stats(start, desk)
        # Will be 90 for right and 270 for left
        to_rotate = (src_ang - facing) % 360
        # Generate the dump command
        route.append(Dump(points[desk], to_rotate == 90))
        # Remove the desk from the set so we don't go back
        del points[desk]
        # Save the route segment
        routes.append(route)
    # Flatten the list
    full_route = sum(routes, [])
    # Report the final location
    full_route.append(Report(start))
    return full_route

# If FLASK_DEBUG isn't defined in the environment build a graph, if it is make
# build_route a nop
try:
    environ['FLASK_DEBUG']
except KeyError:
    _GRAPH = _build_graph()
else:
    build_route = lambda x: []
