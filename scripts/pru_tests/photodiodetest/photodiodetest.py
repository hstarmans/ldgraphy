""" photodiodetest.py - test script for the firestarter board
The laser is turned on
The polygon is spun at a rate of 1000 Hz for 5 seconds
The photodiode is measured for three seconds, if high within these three seconds
test is succesfull, otherwise unsuccesfull.
The laser is turned off.
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

with open("/dev/mem", "r+b") as f:
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    ddr_mem[RAM0_START:RAM0_START + 4] = struct.pack('L', 0)
    
#pypruss.modprobe()                # This only has to be called once pr boot
pypruss.init()                                      
pypruss.open(0)                                     
pypruss.pruintc_init()                              
pypruss.exec_program(0, "./photodiodetest.bin")    
pypruss.wait_for_event(0)                           
pypruss.clear_event(0,pypruss.PRU0_ARM_INTERRUPT)
pypruss.pru_disable(0)                              
pypruss.exit()                            

with open("/dev/mem", "r+b") as f:
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    local = struct.unpack('L', ddr_mem[RAM0_START:RAM0_START + 4])
#TODO: add check if test is succesfull or not
    print(hex(local[0]))




