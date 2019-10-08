#!/usr/bin/python3
""" spinpolygon.py - test script for the firestarter board
It spins the polygon at a rate of 1000 Hz for 5 seconds
"""
from uio.ti.icss import Icss
import Adafruit_BBIO.GPIO as GPIO
from time import sleep


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
GPIO.output("P9_23", GPIO.LOW)
GPIO.cleanup()



