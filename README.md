# mrzsz  (rz and sz for micropython)

A simple file transfer solution for micropython similar to linux zmodem lrzsz aka sz and rz

 - works (properly) over serial, to any board, regardless of RTS<=>RST / DTR<=>GPI0 wiring
 - works over sockets (e.g. telnet) too
 - uses compression, checksums, error handling, and traffic throttling when necessary
 - requires extremely minimal RAM and Flash to work
 - the same files run on micropython, windows, mac, and linux
 - includes optional raw-REPL support for one-sided automatic file send/receive


## How to install

1. Grab the `mrz.py` and `msz.py` files (or the `mrz124.mpy` and `msz124.mpy` binary files if you use micropython v1.24)
2. Put them in /lib on your mcu
3. Put the .py versions someplace in your path on your mac/windows/linux machine


## How to use

1. Receive to your PC from your microcontroller

       # On your PC:
       export PORT=/dev/ttyS26 # use a plain number, like 23 for telnet, to use sockets instead of serial
       mrz --port $PORT filename
       
       # On your Microcontroller *
       import msz

2. Send from your PC to your microcontroller

       # On your Microcontroller * 
       import mrz
       
       # On your PC:
       export PORT=/dev/ttyS26 # use a plain number, like 23 for telnet, to use sockets instead of serial
       msz --port $PORT filename

       
* \* You can omit the microcontroller steps if by adding the --raw switch, which works over serial, and if you're using my [telnetd](https://github.com/gitcnd/telnetd) daemon over sockets
       
       # On your PC:
       export PORT=/dev/ttyS26 # use a plain number, like 23 for telnet, to use sockets instead of serial

       msz --raw --port $PORT filename # send to mcu

       mrz --raw --port $PORT filename # get from mcu


### Protocol details

* mrz triggers an intent to receive by sending the following bytes:

`b"mrz waiting to receive.**\x18B010000100000023be50\x0d\x8a\x11" + b"\x18" * 10 + b"\x08" * 10`

aka

    00000000  72 7a 20 77 61 69 74 69  6e 67 20 74 6f 20 72 65  |rz waiting to re|
    00000010  63 65 69 76 65 2e 2a 2a  18 42 30 31 30 30 30 30  |ceive.**.B010000|
    00000020  31 30 30 30 30 30 30 32  33 62 65 35 30 0d c2 8a  |100000023be50...|
    00000030  11 18 18 18 18 18 18 18  18 18 18 08 08 08 08 08  |................|
    00000040  08 08 08 08 08 0a                                 |......|
   
* msz triggers an intent to send by sending the following bytes:

`b"rz\x0d\x2a\x2a\x18B0000000000000000\x0d\x8a\x11" + b"\x18" * 10 + b"\x08" * 10

aka

    00000000  72 7a 0d 2a 2a 18 42 30  30 30 30 30 30 30 30 30  |rz.**.B000000000|
    00000010  30 30 30 30 30 0d 8a 11  18 18 18 18 18 18 18 18  |00000...........|
    00000020  18 18 08 08 08 08 08 08  08 08 08 08              |............|

* all communications from here-on are 8-bit binary
* all packets begin with two bytes
* if the first byte is \xFF the second byte is a length N and N extra bytes follow. This represents either (1) a status message (completion or error message) to be shown to the user, and indicates the end of the file transfer, or (2) the name of a file to read from or write to (if the first character after the length is \x00)
* if the first 2 byes is \x8000 or above, this indicates a checksum error, and the other side "backs up" N-0x8000 bytes
* if the first 2 bytes are < 0x8000 this indicates a packet length.  This implementation always sends 0x1000 sized packets (4096 bytes) (except for any last one).  
* All packets, including status message and checksum errors, always have 2 extra bytes added on the end, which are the CRC16 of the data which preceded (from and including the first/size bytes).  
* All data and messages sent/received (except for checksum errors) always travels through deflate.RAW

