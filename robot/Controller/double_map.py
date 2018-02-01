class DoubleMap(dict):
    def __init__(self, d):
        dict.__init__(self, d)
        for key in d:
            dict.__setitem__(self, self[key], key)
    def __setitem__(self, key, val):
        if key in self:
            del self[key]
        if val in self:
            del self[val]
        dict.__setitem__(self, key, val)
        dict.__setitem__(self, val, key)

    def __delitem__(self, key):
        dict.__delitem__(dict.__delitem__(self, self[key]))
        dict.__delitem__(dict.__delitem__(self, key))

    def __len__(self):
        return dict.__len__(self) // 2
