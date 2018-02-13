#!/usr/bin/env bash

# Docker command for crosscompiling for the robot

dir=$(pwd)
docker run --rm -v "$dir":/src -w /src alexshand/sdp2018-pathfinder-build-env make robot
