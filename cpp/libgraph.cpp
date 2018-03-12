// Wrappers for the Pathfinder code conversion to python

// Allows the use of std::nothrow to suppress std::bad_alloc exceptions from new
#include <new>
// String construction with <<
#include <sstream>

// std::vector
#include <vector>
// std::begin and std::end
#include <iterator>

// For PyObject
#include <Python.h>

#include "Graph.h"

#include <iostream>
#define print(x) std::cout << x << std::endl

/* C interfaces for the two exposed C++ objects. Each object is converted into a
 * new and delete function and one function per exposed method. The new function
 * should return a pointer to the object created, every other method should
 * accept this pointer in addition to any other required arguments. No
 * functions exposed can throw exceptions */
extern "C" {
    
    /* Edge */

    /* Unless told otherwise python sees any pointer as an integer that it just
     * passes around so there is very little type checking with these
     * functions. */
    Edge* Edge_new(char *left, char *right, int len) {
        /* C++ new can throw a std::bad_alloc exception if it can't allocate the
         * required memory for any reason (lack of available heap memory
         * usually, basically this never happens on non-embedded
         * systems). Passing std::nothrow suppresses this exception, if
         * allocation is going to fail the point we hear about it will be a
         * segfault when python tries to call a method on the object that
         * doesn't exist */
        return new(std::nothrow) Edge(left, right, len);
    }

    void Edge_del(Edge *obj) {
        delete obj;
    }

    /* Despite the argument type being Edge* python will pass void*, it is
     * automatically cast to Edge* before use. The danger with this is ctypes
     * will allow any interger to be passed and leave it up to C++ to cast, at
     * which point the program will likley segfault */
    const char* Edge_left_get(Edge *obj) {
        return obj->left().c_str();
    }

    const char* Edge_right_get(Edge *obj) {
        return obj->right().c_str();
    }

    const int Edge_len_get(Edge *obj) {
        return obj->len();
    }

    /* Odder method, uses the << operator to stringify the object for python to
     * print (Printing from C++ will always print to the 'real' stdout ignoring
     * any redirects the python interpreter makes) */
    const char* Edge_repr(Edge *obj) {
        std::stringstream ss;
        ss << *obj;
        return ss.str().c_str();
    }
    
    /* End Edge */

    /* Graph */

    Graph* Graph_new(Edge** edges, size_t n_edges) {
        /* Potentially inefficient way of converting an array of Edge* to a
         * vector of Edge */
        std::vector<Edge> edges_v;
        for (size_t i = 0; i < n_edges; i++) {
            edges_v.push_back(*(edges[i]));
        }
        return new(std::nothrow) Graph(edges_v);
    }

    void Graph_del(Graph *obj) {
        delete obj;
    }

    const char* Graph_repr(Graph *obj) {
        std::stringstream ss;
        ss << *obj;
        return ss.str().c_str();
    }

    PyObject* Graph_route(Graph *obj, char *start, char *end) {
        std::vector<std::string> path = obj->route(start, end);

        /* Similarly inefficient way of contructing a python list of python
         * strings from a vector of strings */
        PyObject *out = PyList_New(0);
        for (auto item : path) {
            PyList_Append(out, PyUnicode_FromString(item.c_str()));
        }
        return out;
    }
    
    /* End Graph */
}
