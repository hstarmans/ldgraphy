#!/usr/bin/python3
""" home_y.py - test script for the Firestarter
moves the y-motor for a given amount of steps and stepspeed
unless it hits the y-home switch
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
STEPSPEED = 60  # Hz
STEPS = 60 * 10 
DIRECTION = 1

y_direction_output = "P9_20"
GPIO.setup(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)

y_enable = "P9_19"
GPIO.setup(y_enable, GPIO.OUT)
GPIO.output(y_enable, GPIO.HIGH)

# DERIVED
CPU_SPEED = 200E6
INST_PER_LOOP = 2
HALF_PERIOD_STEP = CPU_SPEED/(2*STEPSPEED*INST_PER_LOOP)


class Params( ctypes.Structure ):
    _fields_ = [
            ("steps", ctypes.c_uint32),  
            ("halfperiodstep",    ctypes.c_uint32),
            ("gpio_1_read", ctypes.c_uint32),
]

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
params0 = pruss.core0.dram.map(Params)
params0.steps = round(STEPS)
params0.halfperiodstep = round(HALF_PERIOD_STEP)
pruss.core0.load('home_y.bin')
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(y_enable, GPIO.LOW)
print(pruss.core0.r2)



