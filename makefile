# MAKEFILE is skeleton code for builing and managing the entire
# test-suite for the robot. It allows tests in both python and c++ to
# be used. (Can also manage tests on the arduino.)

# Name of the python interpreter
PYTHON = python3
# Directory where the tests can be found
TESTDIR = ./test
# Search recursively for python files with test in their name
PY_TEST_FILES := $(shell find $(TESTDIR) -type f -name *test*.py 2>/dev/null)

# Directory containing C++ files
CPP_DIR = ./cpp

## Build Targets ##

# Build for Ubuntu 16.04
.PHONY: ubuntu
ubuntu:
	$(MAKE) -C $(CPP_DIR) all

# Build for Travis
.PHONY: travis-build
travis-build:
	$(MAKE) -C $(CPP_DIR) travis-build

## Test Targets ##

.PHONY: test
test: $(PY_TEST_FILES)
	$(MAKE) -C $(CPP_DIR) test

## Helpers ##

# Generic python target, $@ becomes filename
.PHONY: $(PY_TEST_FILES)
$(PY_TEST_FILES): travis-build
	python3 $@

# Dispatch to source specific cleaners
.PHONY: clean
clean:
	$(MAKE) -C $(CPP_DIR) clean
