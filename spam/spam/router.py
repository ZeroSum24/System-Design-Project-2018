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

_MAP = {'S' : {'A' : (36, 0, 180)},
        'A' : {'B' : (84, 0, 180),
               'M' : (71, 90, 270)},
        'B' : {'O' : (0, 270, 90),
               'C' : (74, 0, 180)},
        'C' : {'G' : (71, 90, 270,),
               'D' : (81, 0, 270)},
        'D' : {'E' : (69, 90, 270),
               'U' : (0, 0, 180)},
        'E' : {'F' : (72, 90, 270),
               'V' : (0, 0, 180)},
        'F' : {'X' : (88, 90, 180),
               'W' : (0, 0, 180)},
        'G' : {'I' : (52, 180, 0),
               'H' : (80, 90, 270)},
        'H' : {'J' : (50, 180, 0),
               'X' : (81, 90, 270)},
        'I' : {'Q' : (0, 270, 90),
               'K' : (65, 180, 0)},
        'J' : {'R' : (0, 270, 90),
               'L' : (69, 180, 0)},
        'K' : {'P' : (0, 270, 90),
               'M' : (50, 180, 0)},
        'L' : {'T' : (0, 270, 90),
               'N' : (51, 180, 0)},       
        'M' : {'N' : (80, 90, 270)},
        'N' : {'X' : (194, 90, 0)}}

def _build_graph():
    edges = []
    for start in _MAP:
        for end in _MAP[start]:
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

def _triwise(iterable):
    # Basically the same as above
    a, b, c = itertools.tee(iterable, 3)
    next(b, None)
    next(c, None)
    next(c, None)
    return zip(a, b, c)

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

def build_route(points, start_at='S'):
    # Avoid mutating the argument
    points = dict(points)
    # Algorithm generates several subroutes that must then be unified
    routes = []
    # Start symbol
    start = start_at
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
            route.append(('Report', src))
            # Rotate to the correct angle to exit relative to where we are
            # currently facing
            route.append(('Rotate', (src_ang-facing)%360, 30))
            # Calculate the direction we will be facing upon reaching the next
            # node
            facing = (dest_ang + 180) % 360
            # Move move the required distance down the line
            route.append(('Move', dist, 30))
        # At the end of the route dump the required slots
        # Figure out which direction to dump in
        # Only src_ang is relevant here, the others are just for homogeny
        dist, src_ang, dest_ang = _get_edge_stats(start, desk)
        # Will be 90 for right and 270 for left
        to_rotate = (src_ang - facing) % 360
        # Generate the dump commands
        # True if we are going left. Actually for use in the ToDesk command,
        # also embedded in the FromDesk command temporarily for use in the
        # optimisation step
        is_left = to_rotate == 270
        route.append(('ToDesk', is_left, 90))
        route.append(('Dump', points[desk]))
        route.append(['FromDesk', is_left, 90])
        # Remove the desk from the set so we don't go back
        del points[desk]
        # Save the route segment
        routes.append(route)
    # Flatten the list
    full_route = sum(routes, [])
    # Report the final location
    full_route.append(('Report', start))
    # Optimisation step. Currently the booleans in the ToDesk and FromDesk
    # commands are the same, this causes the robot to enter and exit the desk on
    # the same arc. FromDesk is always followed by a Report then a Rotate, the
    # angle in the Rotate is exclusivly 0 or 180 as desks are always encountered
    # outside of junctions. Should the robot need to rotate 180 at the Rotate
    # command this can instead be encoded by flipping the boolean in FromDesk to
    # make the robot leave the desk on the opposite arc to the one it entered
    # on, the rotates can then be dropped
    to_remove = set()
    for first, _, second in _triwise(full_route):
        # Check we have a FromDesk followed by a Rotate (Ignoring the Report in
        # the middle)
        if first[0] == 'FromDesk' and second[0] == 'Rotate':
            # Log the Rotate for removal
            to_remove.add(second)
            # Fun trick, in python ^ is bitwise xor on ints and logical xor on
            # bools. This flips the boolean iff second.angle == 180 is true
            first[1] ^= second[1] == 180
    # Remove the now useless Rotate instructions
    for instruction in to_remove:
        full_route.remove(instruction)
    return list(map(tuple, full_route))

# If FLASK_DEBUG isn't defined in the environment build a graph, if it is make
# build_route a nop
try:
    environ['FLASK_DEBUG']
except KeyError:
    _GRAPH = _build_graph()
else:
    build_route = lambda x: []
