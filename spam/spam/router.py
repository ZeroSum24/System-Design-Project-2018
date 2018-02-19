#!/usr/bin/env python3

from spam.graph import Edge, Graph
import itertools
from spam.Commands import *

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
    for start in _MAP:
        for end in _MAP[start]:
            edges.append(Edge(start, end, _MAP[start][end][0]))
    return Graph(edges)
_GRAPH = _build_graph()

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
    points = dict(points)
    routes = []
    start = 'S'
    facing = 0
    while points:
        pairs = zip(start * len(points), points)
        nodes = min((_GRAPH.route(*pair) for pair in pairs), key=_path_dist)
        start = nodes[-1]
        route = []
        for src, dest in _pairwise(nodes):
            dist, src_ang, dest_ang = _get_edge_stats(src, dest)
            route.append(Report(src))
            route.append(Rotate((src_ang-facing)%360, 0.3))
            facing = (dest_ang + 180) % 360
            route.append(Move(dist, 0.3))
        route[-1].is_desk = True
        for slot in points[start]:
            route.append(Dump(slot))
        del points[start]
        routes.append(route)
    full_route = sum(routes, [])
    full_route.append(Report(start))
    return full_route

print(build_route({'K' : [1], 'I' : [2], 'H' : [3], 'J' : [4]}))
