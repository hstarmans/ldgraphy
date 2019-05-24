#!/usr/bin/python3
""" createline.py - test script for the firestarter board
It spins the polygon at a rate of 1000 Hz for 5 seconds
while laser channel 1 is enabled, this allows you to measure 
the polygon speed via photodiode and scope
"""
from pyuio.ti.icss import Icss

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()

pruss.core0.load('./createline.bin')
pruss.core0.run()
print('Waiting for core to halt')
while not pruss.core0.halted:
    pass



