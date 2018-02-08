# MAKEFILE is skeleton code for builing and managing the entire
# test-suite for the robot. It allows tests in both python and c++ to
# be used. (Can also manage tests on the arduino.)

# Name of the python interpreter
PYTHON = python3
# Directory where the tests can be found
TESTDIR = ./test
# Search recursivly for python files with test in their name
PY_TEST_FILES := $(shell find $(TESTDIR) -type f -name *test*.py 2>/dev/null)

# Directory containing C++ files
CPP_DIR = ./cpp

## Build Targets ##

# Build for Ubuntu 16.04
.PHONY: ubuntu
ubuntu:
	$(MAKE) -C $(CPP_DIR) all

# Build for robot (Debian Jessie arm64)
.PHONY: robot
robot:
	$(MAKE) -C $(CPP_DIR) robot

## Test Targets ##

# Run all tests that don't require compilation
.PHONY: test
test: $(PY_TEST_FILES)

# Run all tests including compiled tests. Additionally run the tests defined in
# the cpp makefile for the TravisCI Docker Image
.PHONY: test-all
test-all: test cpp
	$(MAKE) -C $(CPP_DIR) test

## Helpers ##

# Generic python target, $@ becomes filename
.PHONY: $(PY_TEST_FILES)
$(PY_TEST_FILES):
	python3 $@

# Dispatch to source specific cleaners
.PHONY: clean
clean:
	$(MAKE) -C $(CPP_DIR) clean
