# Define variables
MPY_CROSS = ../micropython/mpy-cross/build/mpy-cross

# Default target
all: mrz124.mpy msz124.mpy

# Rule to create .mpy from .py
mrz124.mpy: mrz.py
	$(MPY_CROSS) $< -o $@
msz124.mpy: msz.py
	$(MPY_CROSS) $< -o $@

# Clean up
clean:
	rm -f $(OUT)

# Phony targets
.PHONY: all clean

