#!/usr/bin/python3
""" stabilizer.py - test script for the Firestarter board
A single line is uploaded to the laser scanner.
The middle pixel of this line is on and the other pixels are off.
The data is uploaded to the PRU.
The polygon is spun at a rate of x Hz for x seconds.
The position of the laser is determined and a stable line should be projected.
The result of this test is measured with a camera with a neutral density filter
and without a lens.
"""
from pyuio.ti.icss import Icss
from pyuio.uio import Uio
from bidict import bidict
from ctypes import c_uint32

IRQ = 2      # range 2 .. 9
EVENT0 = 19  # range 16 .. 31

# CONSTANTS LASERSCANNER
COMMANDS = ['CMD_EMPTY', 'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
COMMANDS += ['CMD_EXIT', 'CMD_DONE']
COMMANDS = bidict(enumerate(COMMANDS))
ERRORS = ['ERROR_NONE', 'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
ERRORS += ['ERROR_TIME_OVERRUN']
ERRORS = bidict(enumerate(ERRORS))
SCANLINE_DATA_SIZE = 512
QUEUE_LEN = 8
RPM = 2400
FACETS = 4
START_RINGBUFFER = 5

# line
LINE = [2]*SCANLINE_DATA_SIZE
DURATION = 10  # seconds
TOTAL_LINES = RPM*DURATION/60*FACETS


# DATA to send before PRU start
START_LINES = QUEUE_LEN if TOTAL_LINES > QUEUE_LEN else TOTAL_LINES
data = [ERRORS.inv['ERROR_NONE']] + [0]*4
data +=([COMMANDS.inv['CMD_SCAN_DATA']] + LINE)* START_LINES                


pruss = Icss("/dev/uio/pruss/module")
irq = Uio("/dev/uio/pruss/irq%d" % IRQ )

pruss.initialize()

pruss.intc.ev_ch[EVENT0] = IRQ
pruss.intc.ev_clear_one(EVENT0)
pruss.intc.ev_enable_one(EVENT0)

pruss.core0.load('./stabilizer.bin')
pruss.core0.dram.write(data)
pruss.intc.out_enable_one(IRQ)

irq.irq_recv()
event = pruss.intc.out_event[IRQ]
pruss.intc.ev_clear_one(event)


if TOTAL_LINES > QUEUE_LEN:
    TOTAL_LINES -= QUEUE_LEN


byte = START_RINGBUFFER # increased scanline size each loop
response = 1
while True:
    data = [1] + LINE
    irq.irq_recv()
    pruss.intc.ev_clear_one(pruss.intc.out_event[IRQ])
    [command_index] = pruss.core0.dram.map(length = 1, offset = byte)
    try:
        command = COMMANDS[command_index]
        if command == 'CMD_EMPTY':
            pruss.core0.write(data, offset = byte)    
        else:
            print("COMMAND RECEIVED")
            print(COMMANDS[command_index])
            break
    except IndexError:
        print("ERROR, command out of index received")
        print(command_index)
        break
    byte += SCANLINE_DATA_SIZE + 1
    if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
        byte = 1
    if response > TOTAL_LINES:
        break
    response += 1

print("Sent {} lines.".format(response))

error_index = pruss.core0.dram.map(length = 1, offset = 0)[0]
try:
    print("ERROR RECEIVED")
    print(ERRORS[error_index])
except IndexError:
    print("ERROR, error out of index")

sync_fails = pruss.core0.dram.map(c_uint32, offset = 1).value
print("There have been {} sync fails".format(sync_fails))

