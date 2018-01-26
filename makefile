# Name of the python interpreter
PYTHON = python3
# Directory where the tests can be found
TESTDIR = ./test
# Search recursivly for python files with test in their name
PY_TEST_FILES := $(shell find $(TESTDIR) -type f -name *test*.py 2>/dev/null)

# Directory containing C++ files
CPP_DIR = ./cpp

## Build Targets ##

# Build for dice machine
.PHONY: dice
dice:
	$(MAKE) -C $(CPP_DIR) dice

# Build for robot
.PHONY: robot
robot:
	$(MAKE) -C $(CPP_DIR) robot

# Build for vagrant vm
.PHONY: vagrant
vagrant:
	$(MAKE) -C $(CPP_DIR) all

## Test Targets ##

# Run all tests that don't require compilation
.PHONY: test
test: $(PY_TEST_FILES)

# Run all tests including compiled tests
# Additionally run the tests defined in the cpp makefile for the TravisCI Docker Image
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
