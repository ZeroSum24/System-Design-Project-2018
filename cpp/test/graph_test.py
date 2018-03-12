#!/usr/bin/env python3

# Contains a number of unit tests for the pathfinder graphs. {Python version}

import unittest

from sys import path
# The file runs in the cpp directiory, from there this is a relative path to the
# Controller directiory where the graph module is located
path.append('../spam/spam')
from graph import Edge, Graph

ab = Edge("A", "B", 5)
ac = Edge("A", "C", 5)
bc = Edge("B", "C", 5)
bd = Edge("B", "D", 1)
ce = Edge("C", "E", 2)
de = Edge("D", "E", 7)

class GraphTest(unittest.TestCase):

    def test_graph_with_1_edge(self):
        edges = [ab]
        graph = Graph(edges)

        expected = ['A', 'B']

        self.assertEqual(graph.route('A', 'B'), expected)

    def test_graph_with_useless_route(self):
        edges = [ab, ac]
        graph = Graph(edges)

        expected = ['A', 'B']

        self.assertEqual(graph.route('A', 'B'), expected)

    def test_graph_with_longer_route(self):
        edges = [ab, ac, bc]
        graph = Graph(edges)

        expected = ['A', 'B']

        self.assertEqual(graph.route('A', 'B'), expected)

    def test_slightly_more_complex_graph(self):
        edges = [ab, ac, bc, bd, ce, de]
        graph = Graph(edges)

        expected = ['A', 'B', 'D']

        self.assertEqual(graph.route('A', 'D'), expected)

    def test_no_route(self):
        edges = [ab, de]
        graph = Graph(edges)

        expected = []

        self.assertEqual(graph.route("A", "E"), expected);

if __name__ == '__main__':
    unittest.main()
