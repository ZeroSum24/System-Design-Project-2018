//Wrappers for the Pathfinder code convertion to python

#include <iostream>
#include <boost/python.hpp>
#include "Graph.h"

using namespace boost::python;

/* Required to wrap Graph methods that use std::vector and convert too and from
 * boost::python::list */
class GraphWrapper {
    Graph graph;
public:
    explicit GraphWrapper(list &lst) {
        std::vector<Edge> converted;
        for (int i = 0; i < len(lst); i++) {
            converted.push_back(extract<Edge>(lst[i]));
        }
        Graph newGraph(converted);
        this->graph = newGraph;
    }

    // GraphWrapper also needs to provide << for repr() to work
    friend std::ostream& operator<< (std::ostream& out, const GraphWrapper &graph) {
        return out << graph.graph;
    }

    list route(const std::string &start, const std::string &end) const {
        std::vector<std::string> path = graph.route(start, end);
        list ret;
        for (auto node : path) {
            ret.append(node);
        }
        return ret;
    }
};

BOOST_PYTHON_MODULE(libgraph) {
    class_<Edge>("Edge",
                 /* Constructor argument types (Simple types are automatically
                  * converted to their Python equivalents) */
                 init<std::string, std::string, int>())
        /* Wrap getters from C++ in python attributes (Setting these throws an
         * exception) */
        .add_property("left", &Edge::left)
        .add_property("right", &Edge::right)
        .add_property("len", &Edge::len)
        // __repr__() method, uses <<
        .def(repr(self));

    // Need to use a wrapper class for type conversion, see above
    class_<GraphWrapper>("Graph", init<list&>())
        .def(repr(self))
        .def("route", &GraphWrapper::route);
}
