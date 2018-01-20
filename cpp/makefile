CC = g++
CFLAGS = -Wall -std=c++14

INCLUDES = -I./include/

SRCS = $(wildcard *.cpp)
OBJS = $(SRCS:.cpp=.o)

MAIN = dijkstra

.PHONY: all
all: $(MAIN)

$(MAIN): $(OBJS)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJS)

.cpp.o:
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

.PHONY: clean
clean:
	$(RM) $(OBJS)

.PHONY: clean_all
clean_all: clean
	$(RM) $(MAIN)
