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

import pypruss                              # The Programmable Realtime Unit Library
import numpy as np                          # Needed for braiding the pins with the delays
import struct
import mmap

PRU_ICSS = 0x4A300000
PRU_ICSS_LEN = 512 * 1024

RAM0_START = 0x00000000
RAM1_START = 0x00002000
RAM2_START = 0x00012000

# needed for memory read
with open("/dev/mem", "r+b") as f:
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    ddr_mem[RAM0_START:RAM0_START + 4] = struct.pack('L', 0)

# data prep for memory write
steps = [(7 << 22), 0] * 10                 # 10 blinks, this control the GPIO1 pins
delays = [0xFFFFFF] * 20                    # number of delays. Each delay adds 2 instructions, so ~10ns

data = np.array([steps, delays])            # Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()           # Braid the data so every other item is a
data = [20] + list(data)                    # Make the data into a list and add the number of ticks total

    
#pypruss.modprobe()                # This only has to be called once pr boot
pypruss.init()                                      
pypruss.open(0)                                     
pypruss.pruintc_init()
pypruss.pru_write_memory(0, 0, data)        # Load the data in the PRU ram
pypruss.exec_program(0, "./photodiodetest.bin")    
pypruss.wait_for_event(0)                           
pypruss.clear_event(0,pypruss.PRU0_ARM_INTERRUPT)
pypruss.pru_disable(0)                              
pypruss.exit()                            

# read out result and state of the program
with open("/dev/mem", "r+b") as f:
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    local = struct.unpack('L', ddr_mem[RAM0_START:RAM0_START + 4])
#TODO: add check if test is succesfull or not
    print(hex(local[0]))

