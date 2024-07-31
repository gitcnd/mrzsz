#!/usr/bin/env python3

__version__ = '1.0.20240726'  # Major.Minor.Patch

# msz.py / mrz.py
# Created by Chris Drake.
# rz and sz for micropython.  https://github.com/gitcnd/mrzsz

# Usage:-
#
#  mrz
#
#  msz tst.out
#


import sys
import os
import time
import select

# Try to import deflate, otherwise fall back to zlib
USE_DEFLATE = False
try:
    import deflate
    USE_DEFLATE = True
except ImportError:
    import zlib

# Constants
# COMMON_SUFFIX = b"\x0d\x8a\x11" + b"\x18" * 10 + b"\x08" * 10
# MRZ_TRIGGER = b"**\x18B010000100000023be50" + COMMON_SUFFIX
# MSZ_TRIGGER = b"**\x18B0000000000000000" + COMMON_SUFFIX
MRZ_TRIGGER = b"**\x18B010000100000023be50\x0d\x8a\x11" + b"\x18" * 10 + b"\x08" * 10
MSZ_TRIGGER = b"**\x18B0000000000000000\x0d\x8a\x11" + b"\x18" * 10 + b"\x08" * 10

def crc16(data):
    poly = 0x1021
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def send_data(filename, data):
    print(f"{__file__}: Sending data for file {filename}", file=sys.stderr)
    if USE_DEFLATE:
        compressed_data = deflate.DeflateIO(deflate.RAW).write(data)
    else:
        compressed_data = zlib.compress(data, zlib.Z_BEST_COMPRESSION, -zlib.MAX_WBITS)
    packet_size = 4096
    i = 0
    # Send filename as the first packet
    filename_packet = b'\x00' + filename.encode()
    filename_header = len(filename_packet).to_bytes(2, 'big')
    filename_crc = crc16(filename_header + filename_packet).to_bytes(2, 'big')
    sys.stdout.buffer.write(filename_header + filename_packet + filename_crc)
    sys.stdout.buffer.flush()
    while i < len(compressed_data):
        end = min(i + packet_size, len(compressed_data))
        packet = compressed_data[i:end]
        packet_length = len(packet)
        header = packet_length.to_bytes(2, 'big')
        crc = crc16(header + packet).to_bytes(2, 'big')
        sys.stdout.buffer.write(header + packet + crc)
        sys.stdout.buffer.flush()
        i += packet_size
    print(f"{__file__}: Data sent successfully", file=sys.stderr)

def receive_data():
    print(f"{__file__}: Ready to receive data", file=sys.stderr)
    if USE_DEFLATE:
        decompressor = deflate.DeflateIO(deflate.RAW)
    else:
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    filename = None
    file = None
    while True:
        header = sys.stdin.buffer.read(2)
        if not header:
            break
        length = int.from_bytes(header, 'big')
        if length == 0xFFFF:
            message_length = int.from_bytes(sys.stdin.buffer.read(1), 'big')
            message = sys.stdin.buffer.read(message_length)
            crc = sys.stdin.buffer.read(2)
            print(f"{__file__}: Status message: {message.decode()}", file=sys.stderr)
            break
        elif length >= 0x8000:
            bytes_to_backup = length - 0x8000
            crc = sys.stdin.buffer.read(2)
            print(f"{__file__}: Checksum error, backing up {bytes_to_backup} bytes", file=sys.stderr)
        else:
            packet = sys.stdin.buffer.read(length)
            crc = sys.stdin.buffer.read(2)
            if filename is None and packet[0] == 0:
                filename = "test_" + packet[1:].decode()
                file = open(filename, "wb")
                print(f"{__file__}: Receiving file {filename}", file=sys.stderr)
            else:
                if USE_DEFLATE:
                    data = decompressor.read(packet)
                else:
                    data = decompressor.decompress(packet)
                if file:
                    file.write(data)
    if file:
        file.close()
        print(f"{__file__}: File received successfully", file=sys.stderr)

def non_blocking_read():
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.buffer.read(2)
        else:
            return b''

if __name__ == "__main__":
    if "sz" in __file__: # os.path.basename does not exist in micropython
        print(f"{__file__}: Starting msz mode", file=sys.stderr)
        sys.stdout.buffer.write(b'rz\x0d' + MSZ_TRIGGER)
        sys.stdout.buffer.flush()
        if len(sys.argv) < 2:
            print(f"{__file__}: Usage: ./msz.py <filename>", file=sys.stderr)
            sys.exit(1)
        filename = sys.argv[1]
        with open(filename, "rb") as f:
            data = f.read()

        while True:
            sys.stdout.buffer.write(MSZ_TRIGGER)
            sys.stdout.buffer.flush()
            if non_blocking_read() == b'rz':
                sys.stdout.buffer.write(MSZ_TRIGGER)
                sys.stdout.buffer.flush()
                break
            time.sleep(2)
            
        send_data(filename, data)
    else:
        print(f"{__file__}: Starting mrz mode", file=sys.stderr)
        sys.stdout.buffer.write(b'mrz waiting to receive.' + MRZ_TRIGGER)
        sys.stdout.buffer.flush()
        
        while True:
            sys.stdout.buffer.write(MRZ_TRIGGER)
            sys.stdout.buffer.flush()
            if non_blocking_read() == b'**':
                sys.stdout.buffer.write(MRZ_TRIGGER)
                sys.stdout.buffer.flush()
                break
            time.sleep(2)
        
        receive_data()


# socat -d -d pty,raw,echo=0,link=/tmp/pty1 pty,raw,echo=0,link=/tmp/pty2 &
# socat -d -d EXEC:'./msz.py tst.out',pty,raw,echo=0,link=/tmp/pty1 EXEC:'./mrz.py',pty,raw,echo=0,link=/tmp/pty2
