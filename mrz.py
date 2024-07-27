#!/usr/bin/env python

__version__ = '1.0.20240726'  # Major.Minor.Patch

# mrz.py
# Created by Chris Drake.
# rz and sz for micropython.  https://github.com/gitcnd/mrzsz

print("rz waiting to receive.**\x18B010000100000023be50\x0d\x8a\x11" + "\x18" * 10 + "\x08" * 10)
