#!/usr/bin/env python3
import move

move.forward(50, correction=False).join()
move.backward(50).join()
move.left(50).join()
move.right(50).join()

#move.rotater(360, 50)
