#!/usr/bin/python3
""" home_x.py - test script for the Firestarter
moves the x-motor for a given amount of steps and stepspeed
or until it hits the x-home switch
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
STEP_PER_MM = 76.2
STEPSPEED = round(STEP_PER_MM)
STEPS = round(200*STEP_PER_MM) 
DIRECTION = False # False is homing direction 

y_direction_output = "P9_12"
GPIO.setup(y_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(y_direction_output, GPIO.HIGH)
else:
    GPIO.output(y_direction_output, GPIO.LOW)

y_enable = "P9_15"
GPIO.setup(y_enable, GPIO.OUT)
GPIO.output(y_enable, GPIO.LOW)

# DERIVED
CPU_SPEED = 200E6
INST_PER_LOOP = 2
HALF_PERIOD_STEP = round(CPU_SPEED/(2*STEPSPEED*INST_PER_LOOP))


class Params( ctypes.Structure ):
    _fields_ = [
            ("steps", ctypes.c_uint32),  
            ("halfperiodstep", ctypes.c_uint32)
]

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
params0 = pruss.core0.dram.map(Params)
params0.steps = STEPS
params0.halfperiodstep = HALF_PERIOD_STEP
pruss.core0.load('home_y.bin')
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(y_enable, GPIO.HIGH)
if pruss.core0.r2:
    print("Homing failed")
else:
    print("Touched home switch")



