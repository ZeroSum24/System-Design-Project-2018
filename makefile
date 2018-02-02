# Name of the python interpreter
PYTHON = python3
# Directory where the tests can be found
TESTDIR = ./test
# Search recursivly for python files with test in their name
PY_TEST_FILES := $(shell find $(TESTDIR) -type f -name *test*.py)

# Test target, Dependencies are files to run, they should have their own target
# with instructions on how to run
.PHONY: test
test: $(PY_TEST_FILES)

# Generic python target, $@ becomes filename
.PHONY: $(PY_TEST_FILES)
$(PY_TEST_FILES):
	python3 $@
