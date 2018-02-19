// Contains a bunch of macros which generate tests designed to test
// the pathfinder graphs. {C++ version}

#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include <vector>
#include <string>

#include "Graph.h"

using namespace std;

TEST_CASE( "Routing", "Graph::route" ) {

    // Test setup, happens before each section
    Edge ab("A", "B", 5);
    Edge ac("A", "C", 5);
    Edge bc("B", "C", 5);
    Edge bd("B", "D", 1);
    Edge ce("C", "E", 2);
    Edge de("D", "E", 7);

    SECTION( "Graph with 1 edge" ) {
        vector<Edge> edges;
        edges.push_back(ab);
        Graph graph(edges);

        vector<string> expected;
        expected.push_back("A");
        expected.push_back("B");
        
        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Graph with useless route" ) {
        vector<Edge> edges;
        edges.push_back(ab);
        edges.push_back(ac);
        Graph graph(edges);

        vector<string> expected;
        expected.push_back("A");
        expected.push_back("B");

        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Graph with longer route" ) {
        vector<Edge> edges;
        edges.push_back(ab);
        edges.push_back(ac);
        edges.push_back(bc);
        Graph graph(edges);

        vector<string> expected;
        expected.push_back("A");
        expected.push_back("B");

        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Slightly more complex graph" ) {
        vector<Edge> edges;
        edges.push_back(ab);
        edges.push_back(ac);
        edges.push_back(bc);
        edges.push_back(bd);
        edges.push_back(ce);
        edges.push_back(de);
        Graph graph(edges);

        vector<string> expected;
        expected.push_back("A");
        expected.push_back("B");
        expected.push_back("D");

        REQUIRE( graph.route("A", "D") == expected );
    }

    SECTION( "No route" ) {
        vector<Edge> edges;
        edges.push_back(ab);
        edges.push_back(de);
        Graph graph(edges);

        // Empty vector
        vector<string> expected;

        REQUIRE( graph.route("A", "E") == expected );
    }
}
