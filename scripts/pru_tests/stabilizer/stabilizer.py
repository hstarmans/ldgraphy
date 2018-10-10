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

IRQ = 2                  # range 2 .. 9
PRU0_ARM_INTERRUPT = 19  # range 16 .. 31

# laser-scribe-constants.h
COMMANDS = ['CMD_EMPTY', 'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
COMMANDS += ['CMD_EXIT', 'CMD_DONE']
COMMANDS = bidict(enumerate(COMMANDS))
ERRORS = ['ERROR_NONE', 'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
ERRORS += ['ERROR_TIME_OVERRUN']
ERRORS = bidict(enumerate(ERRORS))

CPU_SPEED = 200E6
TICK_DELAY = 75

RPM = 2400
FACETS = 4
FREQUENCY = (RPM*FACETS)//60
TICKS_PER_MIRROR_SEGMENT = CPU_SPEED//(TICK_DELAY*FREQUENCY))
TICKS_START = (20*TICKS_PER_MIRROR_SEGMENT)//100
TICKS_END = (80*TICKS_PER_MIRROR_SEGMENT)//100

SCANLINE_HEADER_SIZE = 1
SCANLINE_DATA_SIZE = (TICKS_END-TICKS_START)//8
SCANLINE_ITEM_SIZE = SCANLINE_HEADER_SIZE + SCANLINE_DATA_SIZE
QUEUE_LEN = 8
ERROR_RESULT_POS = 0
SYNC_FAIL_POS = 1
START_RINGBUFFER = 5
# end of laser_scribe-constants.h

# line
LINE = [2]*SCANLINE_DATA_SIZE
DURATION = 10  # seconds
TOTAL_LINES = RPM*DURATION/60*FACETS

if TOTAL_LINES <= QUEUE_LEN:
    raise Exception("Less than {} lines!".format(QUEUE_LEN))

# DATA to send before PRU start
data = [ERRORS.inv['ERROR_NONE']] + [0]*4
data += ([COMMANDS.inv['CMD_SCAN_DATA']] + LINE)* QUEUE_LEN


pruss = Icss("/dev/uio/pruss/module")
irq = Uio("/dev/uio/pruss/irq%d" % IRQ )

pruss.initialize()

pruss.intc.ev_ch[PRU0_ARM_INTERRUPT] = IRQ
pruss.intc.ev_clear_one(PRU0_ARM_INTERRUPT)
pruss.intc.ev_enable_one(PRU0_ARM_INTERRUPT)

pruss.core0.load('./stabilizer.bin')
pruss.core0.dram.write(data)
pruss.core0.run()


byte = START_RINGBUFFER # increased scanline size each loop
response = 1
while True:
    data = [COMMANDS.inv['CMD_SCAN_DATA']] + LINE
    if response >= TOTAL_LINES - QUEUE_LEN:
        data = [COMMANDS.inv['CMD_EXIT']]
    pruss.intc.out_enable_one(IRQ) 
    irq.irq_recv()
    pruss.intc.ev_clear_one(pruss.intc.out_event[IRQ])
    pruss.intc.out_enable_one(IRQ)
    [command_index] = pruss.core0.dram.map(length = 1, offset = byte)
    try:
        command = COMMANDS[command_index]
        if command == 'CMD_EMPTY':
            pruss.core0.dram.write(data, offset = byte)    
        else:
            print("Command received; {}".format(command))
            break
    except IndexError:
        print("ERROR, command out of index; index {}".format(command_index))
        break
    byte += SCANLINE_ITEM_SIZE
    if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
        byte = START_RINGBUFFER
    response += 1
    if response == TOTAL_LINES:
        break
    if not response%(RPM/60*FACETS):
        print("Sent {} lines".format(response))

while not pruss.core0.halted:
    pass

[command_index] = pruss.core0.dram.map(length = 1, offset = byte)
print("Command received; {}".format(COMMANDS[command_index]))

print("In total, sent {} lines".format(response))

error_index = pruss.core0.dram.map(length = 1, offset = ERROR_RESULT_POS)[0]
try:
    print("Error received; {}".format(ERRORS[error_index]))
except IndexError:
    print("ERROR, error out of index")

sync_fails = pruss.core0.dram.map(c_uint32, offset = SYNC_FAIL_POS).value
print("There have been {} sync fails".format(sync_fails))
