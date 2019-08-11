#!/usr/bin/python3
""" blinklaser1.py - test script for the Firestarter
blinks the laser 3 times with a period of 6 seconds
"""
from pyuio.ti.icss import Icss

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
core = pruss.core0
core.load('on.bin')
core.run()
print('Waiting for core to halt')
while not core.halted:
    pass
