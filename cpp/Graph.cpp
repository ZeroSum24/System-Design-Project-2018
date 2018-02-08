//Actual pathfinder code including Dijkstra's algorithm commented
//below.  See Graph.h (inside include) for the classes of this code

#include "Graph.h"

using std::endl;

// Utility class used in Graph::route
class Node {
    // Name of the node
    std::string m_name;
    // Cost to reach from the current node
    int m_cost = std::numeric_limits<int>::max();
    // Previous vertex in the shortest path between this node and the start node
    std::string m_prev_vertex = "";
    
public:

    /* Though this does nothing it *must* exist or Graph::route will break
     * because std::map is autovivificious and uses the default constructor for
     * new values. The compiler won't generate one if another constructor
     * already exists. */
    Node() {}

    // The real constructor
    explicit Node(const std::string &name):
        m_name(name) {}

    friend std::ostream& operator<< (std::ostream &out, Node &node) {
        out << "Node(name=" << node.m_name << ", cost=" << node.m_cost << ", prev_vertex=" << node.m_prev_vertex << ")";
        return out;
    }

    const std::string name(void) const {
        return m_name;
    }
    
    const int cost(void) const {
        return m_cost;
    }

    void cost(const int cost) {
        m_cost = cost;
    }

    const std::string& prev_vertex() const {
        return m_prev_vertex;
    }

    void prev_vertex(const std::string &cost) {
        m_prev_vertex = cost;
    }
};

// As above, needed for the python wrapper
Edge::Edge() {}

Edge::Edge(const std::string &left, const std::string &right, int len):
        m_left(left), m_right(right), m_len(len) {}

std::ostream& operator<< (std::ostream &out, const Edge &edge) {
    out << edge.m_left;
    for (int i = 0; i < edge.m_len; i++) {
        out << "-";
    }
    out << ">" << edge.m_right;
    return out;
}

const std::string Edge::left(void) const {
    return m_left;
}

const std::string Edge::right(void) const {
    return m_right;
}

const int Edge::len(void) const {
    return m_len;
}

/* Convert the input vector of edges into a more useful nested map
 * representation */
Graph::Graph(const std::vector<Edge> &edges) {
    for (auto edge : edges) {
        m_graph[edge.left()][edge.right()] = edge.len();
        m_graph[edge.right()][edge.left()] = edge.len();
    }
}

std::ostream& operator<< (std::ostream &out, const Graph &graph) {
    auto map = graph.m_graph;
    for (auto edge : map) {
        for (auto end : edge.second) {
            out << edge.first;
            for (int i = 0; i < end.second; i++) {
                out << "-";
            }
            out << ">" << end.first << endl;
        }
    }
    return out;
}

// Algorithm Here
std::vector<std::string> Graph::route(const std::string &start, const std::string &dest) const {
    auto edges = this->m_graph;

    /* Stores the relavent information about each of the nodes, accessed by
     * their name */
    std::map<std::string, Node> nodes;
    std::deque<std::string> unvisited;
    // Fill both
    for (auto edge : edges) {
        std::string name = edge.first;
        Node node(name);
        // Set the cost of the start node to 0
        if (name == start) {
            node.cost(0);
        }
        nodes[name] = node;
        unvisited.push_back(name);
    }

    /* Comparison function (Places the node with the lowest cost at the front of
     * the list) */
    auto comp = [&nodes](std::string left, std::string right) {
        return nodes[left].cost() < nodes[right].cost();
    };

    // Sort the unvisited list
    std::sort(std::begin(unvisited), std::end(unvisited), comp);

    std::set<std::string> visited;
    
    // While there are some unvisited nodes
    while (!unvisited.empty()) {
        // The first one has the lowest cost from the start
        std::string current_name = unvisited.front();
        Node current_node = nodes[current_name];
        
        // Delete it from unvisited
        unvisited.pop_front();
        // Add it to visited
        visited.insert(current_name);

        // Look up the nodes reachable from the current node
        std::map<std::string, int> arcs = edges[current_name];
        // For each of them
        for (auto arc : arcs ) {
            std::string end = arc.first;
            int dist = arc.second;

            // If the end has already been seen do nothing
            if (visited.find(end) != std::end(visited)) {
                continue;
            }

            // Calculate the cost to reach this node by this path (The current
            // cost to get this far + the distance still to travel)
            
            // Check for overflow as we're potentially dealing with one or both
            // operands being INT_MAX
            int current_cost = current_node.cost();
            if ((dist > 0) && (current_cost > std::numeric_limits<int>::max() - dist)) {
                // Will overflow, set the cost to INT_MAX
                current_cost = std::numeric_limits<int>::max();
            } else {
                // Won't overflow, do the calculation
                current_cost = current_node.cost() + dist;
            }

            // If it's smaller than the stored cost update the route
            Node &end_node = nodes[end];
            if (current_cost < end_node.cost()) {
                end_node.cost(current_cost);
                end_node.prev_vertex(current_name);
            }
        }

        // Re-sort the unvisited list
        std::sort(std::begin(unvisited), std::end(unvisited), comp);
    }
    
    // Collect the path by tracking back from the destination
    std::vector<std::string> path;
    Node &node = nodes[dest];

    // If the cost attached to the destination node is INT_MAX then there was no
    // path found from the start node, so return the empty path
    if (node.cost() == std::numeric_limits<int>::max()) {
        return path;
    }
    
    // Otherwise fill the path
    while (node.name() != start) {
        path.push_back(node.name());
        node = nodes[node.prev_vertex()];
    }
    path.push_back(node.name());

    // Path comes out in reverse, return the reversed list
    std::reverse(std::begin(path), std::end(path));
    return path;
}
