// In order to be used as an importable module, the header files need to be 
// held in a managing file. This is that files

#ifndef GRAPH_H
#define GRAPH_H

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <limits>
#include <algorithm>
#include <deque>
#include <set>

class Edge {
    const std::string m_left;
    const std::string m_right;
    const int m_len;
public:
    Edge(const std::string &left, const std::string &right, int len);
    friend std::ostream& operator<< (std::ostream &out, const Edge &edge);
    const std::string left(void) const;
    const std::string right(void) const;
    const int len(void) const;
};

class Graph {
    std::map<std::string, std::map<std::string, int>> m_graph;
public:
    Graph();
    Graph(const std::vector<Edge> &edges);
    friend std::ostream& operator<< (std::ostream &out, const Graph &graph);
    std::vector<std::string> route(const std::string &start, const std::string &end) const;
};

#endif
