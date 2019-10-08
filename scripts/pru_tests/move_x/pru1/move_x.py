#!/usr/bin/python3
""" move_x.py - test script for the Firestarter
moves the x-motor for a given amount of steps and stepspeed
"""
from uio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
XSTEPSPERMM = 76.2 
STEPSPEED = round(1*XSTEPSPERMM)
STEPS =  round(1000*XSTEPSPERMM) 
DIRECTION = False   # false is in direction home

x_direction_pin = "P9_42"
enable_pin = "P9_12"

GPIO.setup(enable_pin, GPIO.OUT)
GPIO.setup(x_direction_pin, GPIO.OUT)

if DIRECTION:
    GPIO.output(x_direction_pin, GPIO.HIGH)
else:
    GPIO.output(x_direction_pin, GPIO.LOW)

GPIO.output(enable_pin, GPIO.LOW)

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

#TODO: doesn't work and mixes up measurement
#GPIO.output(enable_pin, GPIO.HIGH)
