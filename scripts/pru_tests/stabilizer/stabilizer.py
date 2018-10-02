""" stabilizer.py - test script for the firestarter board
A single line is uploaded to the laser scanner.
The middle pixel of this line is on and the other pixels are off.
The data is uploaded to the pru.
The polygon is spun at a rate of x Hz for x seconds.
The position of the laser is determined and a stable line should be projected.
If this is the case the test is succesfull.
"""
from __future__ import print_function

PRUSS0_PRU0_DATARAM = 0
PRUSS0_PRU1_DATARAM = 1
PRUSS0_PRU0_IRAM = 2
PRUSS0_PRU1_IRAM = 3
PRUSS0_SHARED_DATARAM = 4

import pypruss                              
import struct
import mmap
import numpy as np

# BEAGLE BONE CONSTANTS
PRU_ICSS = 0x4A300000
PRU_ICSS_LEN = 512 * 1024

RAM0_START = 0x00000000
RAM1_START = 0x00002000
RAM2_START = 0x00012000

# CONSTANTS LASERSCANNER
COMMANDS = ['CMD_EMPTY', 'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
COMMANDS += ['CMD_EXIT', 'CMD_DONE']
ERRORS = ['ERROR_NONE', 'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC', 'ERROR_TIME_OVERRUN']

# needed for memory read
with open("/dev/mem", "r+b") as f:
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    ddr_mem[RAM0_START:RAM0_START + 4] = struct.pack('L', 0)


# line
scanline_data_size = 512
queue_len = 8
line = [1]*scanline_data_size
RPM = 2400
facets = 4
duration = 30  # seconds

total_lines = 10000*60/duration*facets

# START
start_lines = queue_len if total_lines > queue_len else total_lines
# byte zero is error byte
data = [0]+([1] + line)* start_lines + [3]               
bit_data = (len(data)//4+1)*[0]
for idx, item in enumerate(data):
    bit_data[idx//4]+=item<<(8*(idx%4))

#pypruss.modprobe()                # This only has to be called once pr boot
pypruss.init()                                      
pypruss.open(0)                                     
pypruss.pruintc_init()
pypruss.pru_write_memory(0, 0, bit_data)        # Load the data in the PRU ram
pypruss.exec_program(0, "./stabilizer.bin")    


if total_lines > queue_len:
    total_lines -= queue_len


# continue_line
data = ([1] + line)                
bit_data = (len(data)//4+1)*[0]
for idx, item in enumerate(data):
    bit_data[idx//4]+=item<<(8*(idx%4))


byte = 1 # note byte0 is error
response = 1
while True:
    pypruss.wait_for_event(0)                           
    
    pypruss.clear_event(0, pypruss.PRU0_ARM_INTERRUPT)
    
    # read out result and state of the program
    with open("/dev/mem", "r+b") as f:
        # byte number should be set via amount interrupts received
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
        local = struct.unpack('L', ddr_mem[RAM0_START+byte//4:RAM0_START + byte//4 + 4])
    # START_RINGBUFFER 1 --> ja hij zit in de 1//4 (eerste vier bytes)
    # bit shift to get the first byte
    # bit mask to ignore higher bytes
    command_index = (local[0]>>8*byte)&255
    try:
        command = COMMANDS[command_index]
        if command == 'CMD_EMPTY':
            print("CMD_EMPTY RECEIVED")
            #pypruss.pru_write_memory(0, byte, bit_data)
        else:
            print("COMMAND RECEIVED")
            print(COMMANDS[command_index])
            break
    except IndexError:
        print("ERROR, command out of index received")
        print(command_index)
        break
    byte += queue_len
    if byte > 8*queue_len+1:
        byte = 1
    if response > total_lines:
        break
    response += 1
    print(response)
        
error_index = local[0]&255
try:
    print("ERROR RECEIVED")
    print(ERRORS[error_index])
except IndexError:
    print("Error, out of index")

pypruss.pru_disable(0)                              
pypruss.exit()                            
