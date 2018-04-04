from queue import PriorityQueue

class UniquePriorityQueue(PriorityQueue):
    def __init__(self, maxsize = 0):
        PriorityQueue.__init__(self, maxsize)
        self.values = set()

    def _put(self, item):
        # Called by the put method after aquiring locks etc...
        if item[1] not in self.values:
            PriorityQueue._put(self, item)
            self.values.add(item[1])

    def _get(self):
        # Same for get
        item = PriorityQueue._get(self)
        self.values.remove(item[1])
        return item

    def clear(self):
        # Clear must also clear the values set or the queue will reject values
        # it shouldn't
        self.values = set()
        self.queue.clear()

    def __repr__(self):
        return repr(self.values)
