#include <boost/python.hpp>

#include "Graph.h"

BOOST_PYTHON_MODULE(libgraph) {
    using namespace boost::python;

    class_<Edge>("Edge", init<std::string, std::string, int>());
}
