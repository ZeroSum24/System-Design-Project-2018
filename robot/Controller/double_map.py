"""Subclass of dict, maintain both forward and reverse mappings. Both keys and
   values must be hashable."""

class DoubleMap(dict):
    """Subclass of dict, maintain both forward and reverse mappings. Both keys
       and values must be hashable."""
    def __init__(self, d):
        """Constructor"""
        # Initalise the backing dict with the input dict
        dict.__init__(self, d)
        # For each key in the input dict
        for key in d:
            # Create the reverse mapping
            dict.__setitem__(self, self[key], key)

    def __setitem__(self, key, val):
        """Called when map[key] = val is used"""
        # If either the key or value is already mapped to something else delete
        # the forward and reverse mapping (See below)
        if key in self:
            del self[key]
        if val in self:
            del self[val]
        # Create the new mapping using dict's __setitem__
        dict.__setitem__(self, key, val)
        dict.__setitem__(self, val, key)

    def __delitem__(self, key):
        """Called when del map[key] is used"""
        # Delete the forward and reverse mappings
        dict.__delitem__(dict.__delitem__(self, self[key]))
        dict.__delitem__(dict.__delitem__(self, key))

    def __len__(self):
        """Called when len(map) is used"""
        # Dict __len__ should return the number of keys, the number of 'true'
        # keys is half what dict's __len__ reports
        return dict.__len__(self) // 2
