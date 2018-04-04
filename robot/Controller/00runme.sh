#!/usr/bin/env bash

{
    # -B suppresses bytecode generation which apparently speeds up execution on
    # the bricks
    exec python3 -B ./0control_loop.py
} 2>err.txt # Catch all errors and redirect to err.txt
