#!/usr/bin/python3
""" photodiodemeasure.py - test script for the firestarter board
The laser is turned on
The polygon is spun at a rate of 1000 Hz for 60 seconds
The photodiode should be measured via a scope
The laser is turned off.
"""
from pyuio.ti.icss import Icss

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()

pruss.core0.load('./photodiodemeasure.bin')
pruss.core0.run()
print('Waiting for pru core 0 to finish')
while not pruss.core0.halted:
    pass

