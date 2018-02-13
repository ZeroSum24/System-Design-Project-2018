#!/usr/bin/env bash

# Docker command for removing build outputs

dir=$(pwd)
docker run --rm -v "$dir":/src -w /src alexshand/sdp2018-pathfinder-build-env make clean
