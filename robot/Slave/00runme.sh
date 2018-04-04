#!/usr/bin/env bash

{
    # -B option suppresses bytecode generation which apparently speeds things up
    exec python3 -B ./0main.py
} 2>err.txt
