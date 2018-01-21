#include <iostream>
#include <boost/python.hpp>
#include "Graph.h"

using namespace boost::python;

class GraphWrapper {
    Graph graph;
public:
    GraphWrapper(list& lst) {
        std::vector<Edge> converted;
        for (int i = 0; i < len(lst); i++) {
            converted.push_back(extract<Edge>(lst[i]));
        }
        Graph newGraph(converted);
        this->graph = newGraph;
    }

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
    using self_ns::str;
    
    class_<Edge>("Edge", init<std::string, std::string, int>())
        .add_property("left", &Edge::left)
        .add_property("right", &Edge::right)
        .add_property("len", &Edge::len)
        .def(str(self));

    class_<GraphWrapper>("Graph", init<list&>())
        .def(str(self))
        .def("route", &GraphWrapper::route);
}
