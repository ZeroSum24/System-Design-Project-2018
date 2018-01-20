#include <iostream>
#include <vector>
#include <map>

#include "Graph.h"

using std::cout;
using std::endl;

template <class T>
std::ostream& operator<< (std::ostream &out, std::vector<T> &vec) {
    out << "[ ";
    for (auto item : vec) {
        out << item << " ";
    }
    out << "]";
    return out;
}

// Map
// A------B------C
// |      |      |
// |      |      |
// E------D      |
// |             |
// |             |
// F------G------H
//        |      |
//        |      |
//        |      I
//        |      |
//        |      |
//        J------K

int main(void) {
    // Builtin map
    Edge ab("A", "B", 6);
    Edge bc("B", "C", 6);
    Edge ae("A", "E", 2);
    Edge bd("B", "D", 2);
    Edge ch("C", "H", 5);
    Edge ef("E", "F", 2);
    Edge fg("F", "G", 6);
    Edge gh("G", "H", 6);
    Edge gj("G", "J", 5);
    Edge hi("H", "I", 2);
    Edge ik("I", "K", 2);
    Edge jk("J", "K", 6);
    
    std::vector<Edge> edges;
    edges.push_back(ab);
    edges.push_back(bc);
    edges.push_back(ae);
    edges.push_back(bd);
    edges.push_back(ch);
    edges.push_back(ef);
    edges.push_back(fg);
    edges.push_back(gh);
    edges.push_back(gj);
    edges.push_back(hi);
    edges.push_back(ik);
    edges.push_back(jk);

    Graph graph(edges);

    // Some internal state
    std::string start = "A";
    std::string end = "K";
    
    std::vector<std::string> path = graph.route(start, end);
    cout << path << endl;
    
    return 0;
}
