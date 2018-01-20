#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include <vector>
#include <string>

#include "Graph.h"

using namespace std;

TEST_CASE( "Simple Routing", "Graph::route" ) {
    
    Edge ab("A", "B", 5);
    Edge ac("A", "C", 5);
    Edge bc("B", "C", 5);
    Edge bd("B", "D", 1);
    Edge ce("C", "E", 2);
    Edge de("D", "E", 7);

    SECTION( "Graph with 1 edge" ) {
        vector<Edge> edges = { ab };
        Graph graph(edges);

        vector<string> expected = { "A", "B" };
        
        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Graph with useless route" ) {
        vector<Edge> edges = { ab, ac };
        Graph graph(edges);

        vector<string> expected = { "A", "B" };

        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Graph with longer route" ) {
        vector<Edge> edges = { ab, ac, bc };
        Graph graph(edges);

        vector<string> expected = { "A", "B" };

        REQUIRE( graph.route("A", "B") == expected );
    }

    SECTION( "Slightly more complex graph" ) {
        vector<Edge> edges = { ab, ac, bc, bd, ce, de };
        Graph graph(edges);

        vector<string> expected = { "A", "B", "D" };

        REQUIRE( graph.route("A", "D") == expected );
    }
}
