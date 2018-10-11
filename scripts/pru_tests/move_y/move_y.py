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

y_direction_output = "P9.20"
GPIO.SETUP(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)


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
pruss.core0.load('move_y.bin')
current_time = time.time()
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
