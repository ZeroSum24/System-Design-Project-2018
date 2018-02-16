class Node():
    def __init__(self):
        self.neighbors = []

    def add_neighbor(self, other_node, distance, angle):
        self.neighbors.append((other_node, distance, angle))
