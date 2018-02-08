#!/usr/bin/env python3

from ctypes import *

_COBJ = cdll.LoadLibrary('./libgraph.so')

class Edge:
    _new= _COBJ.Edge_new
    _del = _COBJ.Edge_del
    
    _left_get = _COBJ.Edge_left_get
    _left_get.restype = c_char_p

    _right_get = _COBJ.Edge_right_get
    _right_get.restype = c_char_p

    _len_get = _COBJ.Edge_len_get

    _repr = _COBJ.Edge_repr
    _repr.restype = c_char_p

    def __init__(self, left, right, length):
        self._internal = Edge._new(left, right, length)

    def __del__(self):
        Edge._del(self._internal)

    def __len__(self):
        return Edge._len_get(self._internal)

    def __repr__(self):
        return Edge._repr(self._internal).decode()
    
    @property
    def left(self):
        return Edge._left_get(self._internal).decode()

    @property
    def right(self):
        return Edge._right_get(self._internal).decode()

class Graph:
    _new = _COBJ.Graph_new
    _del = _COBJ.Graph_del

    _repr = _COBJ.Graph_repr
    _repr.restype = c_char_p

    _route = _COBJ.Graph_route
    _route.restype = py_object

    def __init__(self, edges):
        raw_pointers = tuple(map(lambda x: x._internal, edges))
        c_arr = (c_void_p * len(edges))(*raw_pointers)
        self._internal = Graph._new(c_arr)

    def __del__(self):
        Graph._del(self._internal)

    def __repr__(self):
        return Graph._repr(self._internal).decode()

    def route(self, start, end):
        return Graph._route(self._internal, start, end)
