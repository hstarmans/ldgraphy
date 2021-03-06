#!/usr/bin/python3
""" photodiodetest.py - test script for the firestarter board
The laser is turned on
The polygon is spun at a rate of 1000 Hz for 5 seconds
The photodiode is measured for three seconds, if high within these three seconds
test is succesfull, otherwise unsuccesfull.
The laser is turned off.
"""
from ctypes import c_uint32
import Adafruit_BBIO.GPIO as GPIO
from uio.ti.icss import Icss

GPIO.setup("P9_23", GPIO.OUT)
# enable polygon motor
GPIO.output("P9_23", GPIO.LOW)

pruss = Icss('/dev/uio/pruss/module')

pruss.initialize()
pruss.core0.load('./photodiodetest.bin')
pruss.core0.run()
while not pruss.core0.halted:
    pass
byte0 = pruss.core0.dram.map(c_uint32)

return_value = int(byte0.value)

if return_value == 0:
    print("Test successfull")
elif return_value == 1:
    print("Photo diode detector connected but no signal")
else:
    print("Photo diode detector not connected")

# disable polygon motor
GPIO.output("P9_23", GPIO.HIGH)
GPIO.cleanup()




