#!/usr/bin/env bash

dir=$(pwd)
docker run --rm -v "$dir":/src -w /src alexshand/sdp2018-pathfinder-build-env make robot
