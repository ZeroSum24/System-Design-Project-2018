// Wrappers for the Pathfinder code conversion to python

// Allows the use of std::nothrow to suppress std::badalloc exceptions from new
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

/* C interfaces for the two exposed C++ objects. Each object is converted into a
 * new and delete function and one function per exposed method. The new function
 * should return a pointer to the object created, every other method should
 * accept this pointer in addition to any other required arguments. No
 * functions exposed can throw exceptions */
extern "C" {
    
    /* Edge */

    /* Unless told otherwise python sees any pointer as an integer that it just
     * passes around so there is very little type checking with these
     * functions */
    Edge* Edge_new(char *left, char *right, int len) {
        return new(std::nothrow) Edge(left, right, len);
    }

    void Edge_del(Edge *obj) {
        delete obj;
    }

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
     * print (Printing from the C++ will always print to the 'real' stdout
     * ignoring any redirects the python interpreter makes) */
    const char* Edge_repr(Edge *obj) {
        std::stringstream ss;
        ss << *obj;
        return ss.str().c_str();
    }
    
    /* End Edge */

    /* Graph */

    Graph* Graph_new(Edge** edges, int n_edges) {
        std::vector<Edge> edges_v;
        for (int i = 0; i < n_edges; i++) {
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
        PyObject *out = PyList_New(0);
        for (auto item : path) {
            PyList_Append(out, PyUnicode_FromString(item.c_str()));
        }
        return out;
    }
    
    /* End Graph */
}
