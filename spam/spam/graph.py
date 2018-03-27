#!/usr/bin/env python3

from ctypes import *
from os import chdir

# Load the library into memory as a python object, exposed functions in the
# library are methods here. Strictly speaking this is all we need but the C
# interface required for this to work removes all typechecking from either side
# so the objects below are required for safety, also using objects makes the
# code using the library easier
for _ in range(2):
    try:
        chdir("./spam")
    except FileNotFoundError:
        pass
_COBJ = cdll.LoadLibrary('./libgraph.so')

class Edge:
    # Methods to allocate and deallocate the underlying C++ object (See __init__
    # and __del__)
    _new= _COBJ.Edge_new
    _del = _COBJ.Edge_del

    # When ctypes uses a function that returns a pointer it assumes the type is
    # void* because that always works, this is returned to python as an
    # integer. As a string is required the return type of the function must be
    # explicitly set to c_char_p (char*). This will return a byte string which
    # can be decoded into a standard python string.
    _left_get = _COBJ.Edge_left_get
    _left_get.restype = c_char_p

    _right_get = _COBJ.Edge_right_get
    _right_get.restype = c_char_p

    # Edge_len_get returns int so ctypes can properly figure out it's return
    # type
    _len_get = _COBJ.Edge_len_get

    _repr = _COBJ.Edge_repr
    _repr.restype = c_char_p

    def __init__(self, left, right, length):
        """Constructor

        Required Arguments:
        left -- Left node
        right -- Right node
        length -- Length of the edge
        """

        # new returns a Edge* in C++, ctypes sees void* and hands python an int,
        # as such _internal cannot be safely manipulated in python, all accesses
        # must go through the class and be properly delegated to C++. Python
        # won't prevent _internal from being changed, doing so will likey cause
        # a segfault
        self._internal = Edge._new(left, right, length)

    # __del__ is called when the garbage collector deals with an object, it
    # should deallocate the memory held by the C++ object
    def __del__(self):
        Edge._del(self._internal)

    # Called by len()
    def __len__(self):
        return Edge._len_get(self._internal)

    # Called by print()
    def __repr__(self):
        return Edge._repr(self._internal).decode()

    # Property decorator creates an attribute that delegates to the function,
    # i.e these make obj.left and obj.right available on the created objects. As
    # no setters are specified assigning to the attributes raises an Attribute
    # error
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

    # py_object is how ctypes handles PyObject* in the C code, in this case it's
    # a python list
    _route = _COBJ.Graph_route
    _route.restype = py_object

    def __init__(self, edges):
        """Constructor

        Required Arguments:
        edges -- A collection of edges to make up the graph
        """

        # Pull out the _internal pointer from each edge and collect into a tuple
        raw_pointers = tuple(map(lambda x: x._internal, edges))

        # Multiplying a ctypes type by an integer produces a function that
        # accepts a varaible number of arguments and returns a pointer to a C
        # array of that type. * infront of a list/tuple etc destructures it into
        # individual arguments
        c_arr = (c_void_p * len(edges))(*raw_pointers)

        # The Graph_new only sees a pointer so it also needs to be passed the
        # number of edges
        self._internal = Graph._new(c_arr, len(edges))

    def __del__(self):
        Graph._del(self._internal)

    def __repr__(self):
        return Graph._repr(self._internal).decode()

    # No conversion is needed here, a python array is constructed in the C++
    # side using the functions in Python.h
    def route(self, start, end):
        return Graph._route(self._internal, start, end)
