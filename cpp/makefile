# C++ compiler
CC = g++
# All warnings, c++14 features, produce position independent code (Required for
# building a shared library)
CFLAGS = -Wall -std=c++11 -fPIC

# Regular include directory and python3.5 development files
INCLUDES = -I./include/
# Include the relavent dev headers directory for the target platform
# Vagrant machine
ifeq ($(MAKECMDGOALS),all)
INCLUDES += -I/usr/include/python3.5m
endif
# Test include directory
TEST_INCLUDES = -I./test/include/

# Link the correct boost library version
ifeq ($(MAKECMDGOALS),all)
BOOST = -lboost_python-py35
endif

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

.PHONY: dice
dice:

.PHONY: robot
robot:

$(MAIN): $(OBJS)
	# $(OBJS) must appear before $(BOOST) in the command
	$(CC) -shared $(CFLAGS) $(OBJS) $(INCLUDES) $(BOOST) -o $(MAIN)

# Rule for converting .cpp files into .o
.cpp.o:
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -c $< -o $@

# Remove all build outputs
.PHONY: clean
clean:
	$(RM) $(OBJS)
	$(RM) $(TEST_OBJS)
	$(RM) $(MAIN)
	$(RM) $(TEST)

# Build and run the test executable and python tests
.PHONY: test
test: $(TEST) $(MAIN)
	./$(TEST)
	python3 ./test/test.py

$(TEST): $(TEST_OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -o $(TEST) $(TEST_OBJS)
