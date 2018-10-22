#!/usr/bin/python3
""" move_y.py - test script for the Firestarter
moves the y-motor for a given amount of steps and stepspeed
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
YSTEPSPERMM = 76.2 
STEPSPEED = 60  # Hz
STEPS = STEPSPEED * 5 
DIRECTION = False   # false is positive

y_direction_output = "P9_20"
GPIO.setup(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)

y_enable_output = "P9_19"
GPIO.setup(y_enable_output, GPIO.OUT)
GPIO.output(y_enable_output, GPIO.LOW)

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
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(y_enable_output, GPIO.HIGH)
