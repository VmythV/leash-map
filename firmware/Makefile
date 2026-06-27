# LeashMap firmware — host build of the pure-logic core + tests.
# The MCU build (STM32/nRF52 toolchain) is out of scope for this skeleton;
# these targets compile and unit-test the hardware-independent logic on the host.

CC      ?= clang
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic -Iinclude -O1
SRC      = $(wildcard src/*.c)
TESTS    = $(wildcard tests/*.c)
BIN      = build/lm_tests

.PHONY: test clean

test: $(BIN)
	./$(BIN)

$(BIN): $(SRC) $(TESTS)
	@mkdir -p build
	$(CC) $(CFLAGS) $(SRC) $(TESTS) -o $(BIN)

clean:
	rm -rf build
