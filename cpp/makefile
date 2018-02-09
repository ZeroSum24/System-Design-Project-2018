# Builds and tests specifically the pathfinder c++ code.

# Unfortunatly make has no logical or so this mess has to be used to set various
# environment variables of the build system depending on the
# target. $(MAKECMDGOALS) contains a list of targets make is aiming for)

# Standard build Ubuntu 16.04, python 3.5
build_standard =
# For the robot, Debian Jessie, Cross compiled for armel, python 3.4
build_robot =

# Test against the empty string to handle the default target
ifeq ($(MAKECMDGOALS),)
# Any string can go here
build_standard = yes
endif
ifeq ($(MAKECMDGOALS),all)
build_standard = yes
endif
ifeq ($(MAKECMDGOALS),test)
build_standard = yes
endif
ifeq ($(MAKECMDGOALS),robot)
build_robot = yes
endif

# C++ compiler
ifdef build_standard
CC = g++
endif
ifdef build_robot
CC = #TODO
endif

# All warnings, c++11 features, produce position independent code (Required for
# building a shared library)
CFLAGS = -Wall -std=c++11 -fPIC

# Regular include directory
INCLUDES = -I./include/
# Add the required python headers directory
ifdef build_standard
INCLUDES += -I/usr/include/python3.5m/
endif
ifdef build_robot
#TODO
endif

# Test include directory
TEST_INCLUDES = -I./test/include/

# Source files
SRCS := $(wildcard *.cpp)
# Corresponding object files
OBJS := $(SRCS:.cpp=.o)

# Source files required for testing, libgraph.cpp is omitted as it must be built
# by the $(MAIN) rule
TEST_SRCS := $(wildcard ./test/*.cpp) $(filter-out libgraph.cpp,$(SRCS))
# As above
TEST_OBJS := $(TEST_SRCS:.cpp=.o)

# Executables to build for main and test targets
MAIN = libgraph.so
TEST = run_tests

# Build everything (Run with make)
.PHONY: all
all: $(MAIN)
	cp $(MAIN) ../robot/Controller/$(MAIN)

.PHONY: robot
robot: $(MAIN)

$(MAIN): $(OBJS)
	$(CC) -shared $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJS)

# Rule for converting .cpp files into .o
.cpp.o:
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -c $< -o $@

# Remove all build outputs
.PHONY: clean
clean:
	$(RM) $(OBJS)
	$(RM) $(TEST_OBJS)
	$(RM) $(MAIN)
	$(RM) ../robot/Controller/$(MAIN)
	$(RM) $(TEST)

# Build and run the test executable and python tests
.PHONY: test
test: $(TEST) $(MAIN)
	./$(TEST)
	python3 ./test/graph_test.py

$(TEST): $(TEST_OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -o $(TEST) $(TEST_OBJS)
