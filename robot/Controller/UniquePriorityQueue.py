from queue import PriorityQueue

class UniquePriorityQueue(PriorityQueue):
    def __init__(self, maxsize = 0):
        PriorityQueue.__init__(self, maxsize)
        self.values = set()

    def _put(self, item):
        if item[1] not in self.values:
            PriorityQueue._put(self, item)
            self.values.add(item[1])

    def _get(self):
        item = PriorityQueue._get(self)
        self.values.remove(item[1])
        return item
