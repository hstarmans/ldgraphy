#!/usr/bin/python3
""" photodiodetest.py - test script for the firestarter board
The laser is turned on
The polygon is spun at a rate of 1000 Hz for 5 seconds
The photodiode is measured for three seconds, if high within these three seconds
test is succesfull, otherwise unsuccesfull.
The laser is turned off.
"""
from ctypes import c_uint32

from pyuio.ti.icss import Icss

pruss = Icss('/dev/uio/pruss/module')

pruss.initialize()
pruss.core0.load('./photodiodetest.bin')
pruss.core0.run()
while not pruss.core0.halted:
    pass
byte0 = pruss.core0.dram.map(c_uint32)
print(hex(byte0.value))




