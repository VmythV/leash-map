# LeashMap firmware — host build of the pure-logic core + tests.
# The MCU build (STM32/nRF52 toolchain) is out of scope for this skeleton;
# these targets compile and unit-test the hardware-independent logic on the host.

CC       ?= clang
CFLAGS   ?= -std=c11 -Wall -Wextra -Wpedantic -Iinclude -O1
SRC       = $(wildcard src/*.c)
TESTS     = $(wildcard tests/*.c)
BRIDGE_SRC= $(wildcard bridge/*.c)
BIN       = build/lm_tests
BRIDGE    = build/lm_bridge

.PHONY: test bridge clean

test: $(BIN)
	./$(BIN)

$(BIN): $(SRC) $(TESTS)
	@mkdir -p build
	$(CC) $(CFLAGS) $(SRC) $(TESTS) -o $(BIN)

# Host build of the firmware<->cloud bridge (links the real lm_* core with a
# socket HTTP driver). Run via scripts/firmware-bridge-demo.sh.
bridge: $(BRIDGE)

$(BRIDGE): $(SRC) $(BRIDGE_SRC)
	@mkdir -p build
	$(CC) $(CFLAGS) -Ibridge $(SRC) $(BRIDGE_SRC) -o $(BRIDGE) -lm

clean:
	rm -rf build
