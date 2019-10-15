#!/usr/bin/python3
""" spinpolygon.py - test script for the firestarter board
It spins the polygon at a rate of x Hz for 5 seconds
"""
from uio.ti.icss import Icss
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P9_23", GPIO.OUT)
# enable motor
GPIO.output("P9_23", GPIO.LOW)

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
pruss.core0.load('./spinpolygon.bin')
pruss.core0.run()
print('Waiting for core to halt')
while not pruss.core0.halted:
    pass
# disable motor
GPIO.output("P9_23", GPIO.HIGH)



