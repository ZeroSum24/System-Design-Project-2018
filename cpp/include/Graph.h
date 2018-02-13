/* Actual classes implemented by Graph.cpp are here, this allows them to be
 * imported by other files */

#ifndef GRAPH_H
#define GRAPH_H

#include <iostream>  // std::endl
#include <string>    // std::string
#include <vector>    // std::vector
#include <map>       // std::map
#include <limits>    // std::numeric_limits
#include <algorithm> // std::sort, std::reverse
#include <deque>     // std::deque
#include <set>       // std::set

class Edge {
    const std::string m_left = "";
    const std::string m_right = "";
    const int m_len = 0;
public:
    Edge();
    Edge(const std::string &left, const std::string &right, int len);
    friend std::ostream& operator<< (std::ostream &out, const Edge &edge);
    const std::string left(void) const;
    const std::string right(void) const;
    const int len(void) const;
};

class Graph {
    std::map<std::string, std::map<std::string, int>> m_graph;
public:
    Graph(const std::vector<Edge> &edges);
    friend std::ostream& operator<< (std::ostream &out, const Graph &graph);
    std::vector<std::string> route(const std::string &start, const std::string &end) const;
};

#endif
