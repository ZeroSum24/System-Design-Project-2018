#!/usr/bin/env python3

import unittest
import dummy

class DummyTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(dummy.add(5, 17), 5 + 17)

if __name__ == '__main__':
    unittest.main()
