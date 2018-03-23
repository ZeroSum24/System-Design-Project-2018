#!/usr/bin/env bash

{
exec python3 ./0control_loop.py
} >>err.txt 2>&1
