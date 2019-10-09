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
from ctypes import c_uint32

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
TICKS_PER_MIRROR_SEGMENT = 12500 
QUEUE_LEN = 8
ERROR_RESULT_POS = 0
SYNC_FAIL_POS = 1
START_RINGBUFFER = 5
SINGLE_FACET = False
DURATION = 10 # seconds
# end of laser_scribe-constants.h

# line for multiple facets
# data_byte = [int('10000000', 2)]*1+[int('00000000',2)]*31  # left bit, bit 7 read out first
# line for single facet
data_byte = [int('10000000', 2)]*1+[int('00000000',2)]*31
# line totally on; to detect edges
#data_byte = [int('11111111', 2)]*16
LINE = data_byte*(SCANLINE_DATA_SIZE//32)+SCANLINE_DATA_SIZE%32*[int('00000000',2)]
print("length line is "+str(len(LINE)))
TOTAL_LINES = RPM*DURATION/60*FACETS


# Steps
STEPSPERMM = 76.2
MICROSTEPPING = 1
#TOTAL_LINES = round(10*STEPSPERMM)
DIRECTION = False # False is in the homing direction

y_direction_output = "P8_15"
GPIO.setup(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)


y_enable_output = "P8_11"
GPIO.setup(y_enable_output, GPIO.OUT)
GPIO.output(y_enable_output, GPIO.HIGH) # motor disabled


if TOTAL_LINES <= QUEUE_LEN:
    raise Exception("Less than {} lines!".format(QUEUE_LEN))

# DATA to send before PRU start
data = [ERRORS.inv['ERROR_NONE']] + [0]*4
data += ([COMMANDS.inv['CMD_SCAN_DATA']] + LINE)* QUEUE_LEN

# ENABLE polygon motor
polygon_enable = "P9_23"
GPIO.setup(polygon_enable, GPIO.OUT)
GPIO.output(polygon_enable, GPIO.LOW)


pruss = Icss("/dev/uio/pruss/module")
irq = Uio("/dev/uio/pruss/irq%d" % IRQ, blocking=False)

pruss.initialize()

pruss.intc.ev_ch[PRU0_ARM_INTERRUPT] = IRQ
pruss.intc.ev_clear_one(PRU0_ARM_INTERRUPT)
pruss.intc.ev_enable_one(PRU0_ARM_INTERRUPT)

pruss.core0.load('./determinejitter.bin')
pruss.core0.dram.write(data)
pruss.core0.run()
print("running core and uploaded data")

byte = START_RINGBUFFER # increased scanline size each loop
response = 1
# you read through ring buffer, it is extended by one to read out hsync time

# for each facet the sync time is determined, this should be the ticks per mirror segment

hsync_times = []
while True and not pruss.core0.halted:
    if SINGLE_FACET and (response%4!=0):
        data = [COMMANDS.inv['CMD_SCAN_DATA']] + SCANLINE_DATA_SIZE*[0]
    else:
        data = [COMMANDS.inv['CMD_SCAN_DATA']] + LINE
    if response >= TOTAL_LINES - QUEUE_LEN:
        data = [COMMANDS.inv['CMD_EXIT']]
    pruss.intc.out_enable_one(IRQ) 
    while True:
        result  = irq.irq_recv()
        if result:
            break
        else:
            sleep(1E-3)          
    pruss.intc.ev_clear_one(pruss.intc.out_event[IRQ])
    pruss.intc.out_enable_one(IRQ)
    [command_index] = pruss.core0.dram.map(length = 1, offset = byte)
    hsync_times.append(pruss.core0.dram.map(c_uint32, offset = 1).value)
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
# TODO: sync fails doesn't work
#sync_fails = pruss.core0.dram.map(c_uint32, offset = SYNC_FAIL_POS).value
#print("There have been {} sync fails".format(sync_fails))
# disable motors
GPIO.output(y_enable_output, GPIO.HIGH)  
GPIO.output(polygon_enable, GPIO.HIGH)
# The expected hsync time, see constants TICKS PER MIRROR SEGMENT
print("The expected hsync time is {}".format(TICKS_PER_MIRROR_SEGMENT))
print("The facet series are")
# print the first 16 hsync times
if len(hsync_times)<10:
    print("Not enough sync times collected")
    raise SystemExit

# Goal is to print facet times by cohort, say the facet times are 2 5 6 3
# it would print, i.e. it should order them so you can see if there is a regularity 
#              2 2 2 2 
#              5 5 5 5
#              6 6 6 6 
#              3 3 3 3

offset = 100

for item in range(0+offset,16*8+offset,16):
    print("Item: {}".format(item))
    for i in range(0,4):
        facet_list = ""
        for j in range(0,20,4):
            facet_list+=str(hsync_times[item+i+j])+" "
        print(facet_list)

# let's see if we can create two bins, one for a single facet and the rest for the others

hsync_times = hsync_times[offset:]

bins=hsync_times[1:FACETS]
cntrs = [0,0]
for time in hsync_times:
    if time<12400:
        cntrs[0]+=1
    else:
        cntrs[1]+=1
print("The counters are {}".format(cntrs))
# sum
sum_cntrs = 0
for cntr in cntrs:
    sum_cntrs += cntr

difference = len(hsync_times)//4-cntrs[0]

if abs(difference)>2:
    print("Difference of bin times seems incorrect {}".format(difference))
else:
    print("Test passed, can bin all times")



