#!/usr/bin/python3
""" move_x.py - test script for the Firestarter
moves the x-motor for a given amount of steps and stepspeed
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
STEPSPEED = 60  # Hz
STEPS = 60 * 10 
DIRECTION = 1

x_direction_output = "P9_12"
GPIO.setup(x_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(x_direction_output, GPIO.HIGH)
else:
    GPIO.output(x_direction_output, GPIO.LOW)

x_enable_output = "P9_15"
GPIO.setup(x_enable_output, GPIO.OUT)
GPIO.output(x_enable_output, GPIO.LOW)

# DERIVED
CPU_SPEED = 200E6
INST_PER_LOOP = 2
HALF_PERIOD_STEP = CPU_SPEED/(2*STEPSPEED*INST_PER_LOOP)


class Params( ctypes.Structure ):
    _fields_ = [
            ("steps", ctypes.c_uint32),  
            ("halfperiodstep",    ctypes.c_uint32),
]

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
params0 = pruss.core0.dram.map(Params)
params0.steps = round(STEPS)
params0.halfperiodstep = round(HALF_PERIOD_STEP)
pruss.core0.load('move_x.bin')
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(x_enable_output, GPIO.HIGH)
