# Builds and tests specifically the pathfinder c++ code.

# Unfortunatly make has no logical or so this mess has to be used to set various
# environment variables of the build system depending on the target.

# C++ compiler
CC = g++

# All warnings, c++11 features, produce position independent code (Required for
# building a shared library)
CFLAGS = -Wall -std=c++11 -fPIC

# Regular include directory
INCLUDES = -I./include/ -I/usr/include/python3.5m/

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
	python3 ./test/test.py

$(TEST): $(TEST_OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -o $(TEST) $(TEST_OBJS)
