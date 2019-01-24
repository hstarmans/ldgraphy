#!/usr/bin/python3
""" spinpolygon.py - test script for the firestarter board
It spins the polygon at a rate of 1000 Hz for 5 seconds
"""
from pyuio.ti.icss import Icss

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()

pruss.core0.load('./spinpolygon.bin')
pruss.core0.run()
print('Waiting for core to halt')
while not pruss.core0.halted:
    pass



