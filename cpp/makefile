# C++ compiler
CC = g++
# All warnings, c++14 features
CFLAGS = -Wall -std=c++14 -fPIC

# Regular include directory
INCLUDES = -I./include/ -I/usr/include/python3.5m
# Test include directory
TEST_INCLUDES = -I./test/include/

BOOST = -lboost_python-py35

# Source files
SRCS := $(wildcard *.cpp)
# Corresponding object files
OBJS := $(SRCS:.cpp=.o)

# Source files required for testing
TEST_SRCS := $(wildcard ./test/*.cpp) $(filter-out libgraph.cpp,$(SRCS))
# As above
TEST_OBJS := $(TEST_SRCS:.cpp=.o)

# Executables to build for main and test targets
MAIN = libgraph.so
TEST = run_tests

# Build everything (Run with make)
.PHONY: all
all: $(MAIN)

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

# Build and run the test executable
.PHONY: test
test: $(TEST)
	./$(TEST)

$(TEST): $(TEST_OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) $(TEST_INCLUDES) -o $(TEST) $(TEST_OBJS)
