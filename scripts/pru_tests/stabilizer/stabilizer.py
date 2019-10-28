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
from time import sleep
from ctypes import c_uint32, c_uint16, c_uint8, Structure

from uio.ti.icss import Icss
from uio.device import Uio
from bidict import bidict
import Adafruit_BBIO.GPIO as GPIO

IRQ = 2                  # range 2 .. 9
PRU0_ARM_INTERRUPT = 19  # range 16 .. 31

# constants needed from  laser-scribe-constants.h
COMMANDS = ['CMD_EMPTY', 'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
COMMANDS += ['CMD_EXIT', 'CMD_DONE']
COMMANDS = bidict(enumerate(COMMANDS))
ERRORS = ['ERROR_NONE', 'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
ERRORS += ['ERROR_TIME_OVERRUN']
ERRORS = bidict(enumerate(ERRORS))
RPM = 2400
FACETS = 4
SCANLINE_DATA_SIZE = 937 
SCANLINE_HEADER_SIZE = 1
SCANLINE_ITEM_SIZE = SCANLINE_HEADER_SIZE + SCANLINE_DATA_SIZE
QUEUE_LEN = 8
ERROR_RESULT_POS = 0
SYNC_FAIL_POS = 1
START_RINGBUFFER = 5
SINGLE_FACET = False
DURATION = 30/4*2 # seconds
STEPSPERMM = 76.2
MICROSTEPPING = 1 
ENABLED = False  # False movement is disabled
DIRECTION = True # False in the homing direction
y_direction_output = "P8_15"
y_enable_output = "P9_12"

# line for multiple facets
# data_byte = [int('10000000', 2)]*1+[int('00000000',2)]*31  # left bit, bit 7 read out first
# line for single facet
data_byte = [int('10000000', 2)]*1+[int('00000000',2)]*31
# line totally on; to detect edges
#data_byte = [int('11111111', 2)]*16
LINE = data_byte*(SCANLINE_DATA_SIZE//32)+SCANLINE_DATA_SIZE%32*[int('00000000',2)]
print("length line is "+str(len(LINE)))
TOTAL_LINES = RPM*DURATION/60*FACETS

GPIO.setup(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)


y_enable_output = "P9_12"
GPIO.setup(y_enable_output, GPIO.OUT)
if ENABLED:
    GPIO.output(y_enable_output, GPIO.LOW) # motor on
else:
    GPIO.output(y_enable_output, GPIO.HIGH)


# ENABLE polygon motor
polygon_enable = "P9_23"
GPIO.setup(polygon_enable, GPIO.OUT)
GPIO.output(polygon_enable, GPIO.LOW)

# map and set parameters
class Variables( Structure ):
    _fields_ = [
            ("ringbuffer_size", c_uint32),  
            ("item_size", c_uint32),
            ("start_sync_after", c_uint32),
            ("global_time", c_uint32),
            ("polygon_time", c_uint32),
            ("wait_countdown", c_uint32),
            ("hsync_time", c_uint32),
            ("last_hsync_time", c_uint32),
            ("sync_laser_on_time", c_uint32),
            ("item_start", c_uint32),
            ("item_pos", c_uint32),
            ("state", c_uint16),
            ("bit_loop", c_uint8),
            ("last_hsync_bit", c_uint8),
            ("single_facet", c_uint16),
            ("current_facet", c_uint16),
        ]


pruss = Icss("/dev/uio/pruss/module")
irq = Uio("/dev/uio/pruss/irq%d" % IRQ, blocking=False)

pruss.initialize()

pruss.intc.ev_ch[PRU0_ARM_INTERRUPT] = IRQ
pruss.intc.ev_clear_one(PRU0_ARM_INTERRUPT)
pruss.intc.ev_enable_one(PRU0_ARM_INTERRUPT)

pruss.core0.load('./stabilizer.bin')

params0 = pruss.core0.dram.map(Variables)
if SINGLE_FACET:
    params0.single_facet = 1
else:
    params0.single_facet = 0

pruss.core0.run()
print("running core and uploaded data")

byte = START_RINGBUFFER # increased scanline size each loop
response = 1

while True and not pruss.core0.halted:
    data = [COMMANDS.inv['CMD_SCAN_DATA']] + LINE
    if response >= TOTAL_LINES:
        data = [COMMANDS.inv['CMD_EXIT']]
    pruss.intc.out_enable_one(IRQ) 
    while True:
        result = irq.irq_recv()
        if result:
            break
        else:
            sleep(1E-3)
    pruss.intc.ev_clear_one(pruss.intc.out_event[IRQ])
    [command_index] = pruss.core0.dram.map(length = 1, offset = byte)
    try:
        command = COMMANDS[command_index]
        if command == 'CMD_EMPTY':
            pruss.core0.dram.write(data, offset = byte)    
        else:
            break
    except IndexError:
        print("ERROR, command out of index; index {}".format(command_index))
        break
    byte += SCANLINE_ITEM_SIZE
    if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
        byte = START_RINGBUFFER    
    if response == TOTAL_LINES:
        break
    response += 1
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
# disable motors
GPIO.output(y_enable_output, GPIO.HIGH)  
GPIO.output(polygon_enable, GPIO.HIGH)
