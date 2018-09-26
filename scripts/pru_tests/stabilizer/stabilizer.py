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

#TODO: replace with real test data
# data prep for memory write
#  START with error out of bounds
#  SCAN_DATA COMMAND
#  FINISH with EXIT command
data = [0] + [1] * 1000*100 + [3]                
bit_data = (len(data)//4+1)*[0]
for idx, item in enumerate(data):
    bit_data[idx//4]+=item<<(8*(idx%4))

#pypruss.modprobe()                # This only has to be called once pr boot
pypruss.init()                                      
pypruss.open(0)                                     
pypruss.pruintc_init()
pypruss.pru_write_memory(0, 0, bit_data)        # Load the data in the PRU ram
pypruss.exec_program(0, "./stabilizer.bin")    
pypruss.wait_for_event(0)                           
pypruss.clear_event(0, pypruss.PRU0_ARM_INTERRUPT)
pypruss.pru_disable(0)                              
pypruss.exit()                            

# read out result and state of the program
with open("/dev/mem", "r+b") as f:
    # byte number should be set via amount interrupts received
    byte = 1
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    local = struct.unpack('L', ddr_mem[RAM0_START+byte//4:RAM0_START + byte//4 + 4])
    # START_RINGBUFFER 1 --> ja hij zit in de 1//4 (eerste vier bytes)
    # bit shift to get the first byte
    # bit mask to ignore higher bytes
    command_index = (local[0]>>8*byte)&255
    try:
        print("COMMAND RECEIVED")
        print(COMMANDS[command_index])
    except IndexError:
        print("ERROR, command out of index received")
        print(command_index)
    error_index = local[0]&255
    if error_index:
        try:
            print("ERROR RECEIVED")
            print(ERRORS[error_index])
        except IndexError:
            print("Error, out of index")
    else:
        print("No error received")




    # vul drie in 

