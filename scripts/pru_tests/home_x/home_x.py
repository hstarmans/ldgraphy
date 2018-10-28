#!/usr/bin/python3
""" home_x.py - test script for the Firestarter
moves the y-motor for a given amount of steps and stepspeed
unless it hits the y-home switch
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
STEPS_PER_MM = 76.2
STEPSPEED = round(4*STEPS_PER_MM)
STEPS = round(200*STEPS_PER_MM)
DIRECTION = False  # true is to home

x_direction_output = "P9_20"
GPIO.setup(x_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(x_direction_output, GPIO.HIGH)
else:
    GPIO.output(x_direction_output, GPIO.LOW)

x_enable = "P9_19"
GPIO.setup(x_enable, GPIO.OUT)
GPIO.output(x_enable, GPIO.LOW)

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
pruss.core0.load('home_x.bin')
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(x_enable, GPIO.HIGH)
if pruss.core0.r2:
    print("Homing failed, did not touch switch")
else:
    print("Homing successfull")



